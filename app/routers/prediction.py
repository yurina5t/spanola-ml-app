from fastapi import APIRouter, HTTPException, Depends, status
from sqlmodel import Session, select
from typing import List, Literal
import logging

from database.database import get_session
from dependencies.auth import get_current_user, TokenData
from dependencies.authz import self_or_admin
from models.user import User
from models.wallet import Wallet
from models.theme import Theme
from models.task_log import TaskResult
from services.crud.task_log import log_task
from services.crud.wallet import deduct_from_wallet, top_up_wallet
from services.generation.spanish_comic import SpanishComicModel
from services.crud.prediction_log import log_prediction, get_predictions_by_user
from schemas.prediction import (
    PredictRequest, 
    PredictResponse, 
    PredictionHistoryItem, 
)

logger = logging.getLogger(__name__)
predict_route = APIRouter(prefix="/predictions", tags=["predictions"])

COST_PER_PREDICT = 1.0  # базовая стоимость запроса


@predict_route.post(
    "/",
    response_model=PredictResponse,
    status_code=status.HTTP_200_OK,
    summary="Сделать предсказание (сгенерировать задание)",
    description="енерация бесплатна; списание кредитов только если is_bonus=true",
)
def predict(
    req: PredictRequest, 
    session: Session = Depends(get_session),
    token: TokenData = Depends(get_current_user),
) -> PredictResponse:
    """
    Сгенерировать задание (комикс) и списать кредиты у указанного пользователя.
    Гарантия: если ошибка произошла ПОСЛЕ списания, средства будут возвращены.
    Доступ: сам пользователь или администратор.
    """
    # доступ только self или admin 
    if not (token.is_admin or token.user_id == req.user_id):
        raise HTTPException(status_code=403, detail="Можно предсказывать только для себя")
    
    # 1) Проверяем пользователя, кошелёк, тему
    user = session.get(User, req.user_id)
    if not user:
        logger.warning("Предсказание: пользователь не найден, id=%s", req.user_id)
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    wallet = session.exec(select(Wallet).where(Wallet.user_id == user.id)).first()
    if not wallet:
        logger.warning("Предсказание: кошелёк не найден, user_id=%s", user.id)
        raise HTTPException(status_code=404, detail="Кошелёк не найден")

    theme = session.get(Theme, req.theme_id)
    if not theme:
        logger.warning("Предсказание: тема не найдена, theme_id=%s", req.theme_id)
        raise HTTPException(status_code=404, detail="Тема не найдена")


    # 2) По умолчанию генерация бесплатна
    credits_spent = 0.0
    did_deduct = False

    # Если это бонусный комикс — списываем COST_PER_PREDICT
    if req.is_bonus:
        try:
            deduct_from_wallet(user_id=user.id, amount=COST_PER_PREDICT, session=session)
            credits_spent = float(COST_PER_PREDICT)
            did_deduct = True
            logger.info("Списаны кредиты за БОНУС: user_id=%s, amount=%s", user.id, COST_PER_PREDICT)
        except ValueError as e:
            msg = str(e)
            # маппинг: не найден -> 404, недостаточно -> 409, прочее -> 400
            if "не найден" in msg.lower():
                code = 404
            elif "недостаточно" in msg.lower():
                code = 409
            else:
                code = 400
            logger.warning("Списание не удалось: user_id=%s, error=%s", user.id, msg)
            raise HTTPException(status_code=code, detail=msg)

    # 3) Делаем предикт + логируем; при любой ошибке возвращаем средства
    model = SpanishComicModel()
    try:
        # Генерация задания (комикса/упражнения)
        task_result: TaskResult = model.generate_task(theme, is_bonus=req.is_bonus)

        # Лог предсказания
        log_prediction(
            user_id=user.id,
            model_name=model.name,
            theme_name=theme.name,
            difficulty=task_result.difficulty,
            session=session,           #внутри CRUD делается commit+refresh
        )
        # Лог задачи
        log_task(
            user_id=user.id,
            task_description=task_result.explanation,
            model_name=model.name,
            credits_spent=credits_spent,
            difficulty=task_result.difficulty,
            vocabulary=task_result.vocabulary,
            explanation=task_result.explanation,
            is_correct=False,  #на этапе генерации ответа ещё нет, поэтому ставим False
            session=session,
        )

        session.refresh(wallet)

        logger.info(
            "Предсказание выполнено: user_id=%s, theme_id=%s, cost=%s", 
            user.id, 
            theme.id, 
            credits_spent,
        )

        return PredictResponse(
            model_name=model.name,
            theme_name=theme.name,
            difficulty=task_result.difficulty,
            explanation=task_result.explanation,
            vocabulary=task_result.vocabulary,
            credits_spent=credits_spent,
            balance_after=wallet.balance,
        )
    
    except HTTPException:
        # Возврат средств и проброс исходной ошибки
        if did_deduct:
            try:
                top_up_wallet(user_id=user.id, amount=COST_PER_PREDICT, session=session)
                logger.info("Средства возвращены после ошибки предсказания: user_id=%s, amount=%s", user.id, COST_PER_PREDICT)
            except Exception as re:
                logger.error("Не удалось вернуть средства после ошибки предсказания: user_id=%s, err=%s", user.id, str(re))
            raise
    except Exception as e:
        # Любая другая ошибка: возврат средств + ошибка 500
        if did_deduct:
            try:
                top_up_wallet(user_id=user.id, amount=COST_PER_PREDICT, session=session)
                logger.info("Средства возвращены после ошибки предсказания: user_id=%s, amount=%s", user.id, COST_PER_PREDICT)
            except Exception as re:
                logger.error("Не удалось вернуть средства после ошибки предсказания: user_id=%s, err=%s", user.id, str(re))
            logger.exception("Ошибка предсказания: %s", str(e))
            raise HTTPException(status_code=500, detail="Ошибка предсказания")


@predict_route.get(
    "/history/{user_id}",
    response_model=List[PredictionHistoryItem],
    summary="История предсказаний пользователя",
    description="Возвращает последние записи из PredictionLog (доступ: владелец или админ)",
)
def prediction_history(
    user_id: int, 
    limit: int = 100, 
    session: Session = Depends(get_session),
    _: TokenData = Depends(self_or_admin),
) -> List[PredictionHistoryItem]:
    """
    История предсказаний для пользователя.
    """
    rows = get_predictions_by_user(user_id, session)
    # т.к. CRUD возвращает всё без сортировки/лимита — режем здесь
    rows = sorted(rows, key=lambda r: r.recommended_at, reverse=True)[:limit]
    logger.info("История предсказаний: user_id=%s, rows=%s", user_id, len(rows))
    return [PredictionHistoryItem.model_validate(r) for r in rows]
