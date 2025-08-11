from fastapi import APIRouter, HTTPException, Depends, status
from sqlmodel import Session, select
from datetime import datetime, timezone
from typing import List
import logging

from database.database import get_session
from models.user import User
from models.wallet import Wallet
from models.theme import Theme
from models.task_log import TaskLog, TaskResult
from services.crud.task_log import log_task
from models.transaction_log import TransactionLog, OperationType
from services.generation.spanish_comic import SpanishComicModel

from services.crud.prediction_log import (
    log_prediction,
    get_predictions_by_user,
)

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
    description="Списывает кредиты, генерирует задание и пишет логи"
)
def predict(req: PredictRequest, session: Session = Depends(get_session)) -> PredictResponse:
    """
    Сгенерировать задание (комикс) и списать кредиты у указанного пользователя.
    """
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

    if wallet.balance < COST_PER_PREDICT:
        logger.info("Недостаточно баллов для предсказания: user_id=%s, need=%s, have=%s",
                    user.id, COST_PER_PREDICT, wallet.balance)
        raise HTTPException(status_code=409, detail="Недостаточно баллов")

    # 2) Списываем кредиты + лог транзакции (одним коммитом)
    wallet.balance -= COST_PER_PREDICT
    session.add(wallet)
    session.add(TransactionLog(
        user_id=user.id,
        amount=COST_PER_PREDICT,
        operation=OperationType.debit,
        reason="prediction",
        timestamp=datetime.now(timezone.utc),
    ))

    # 3) Генерируем задание
    model = SpanishComicModel()
    task_result: TaskResult = model.generate_task(theme, is_bonus=req.is_bonus)

    # 4) Лог предсказания и лог задачи
    log_prediction(
        user_id=user.id,
        model_name=model.name,
        theme_name=theme.name,
        difficulty=task_result.difficulty,
        session=session,           #внутри CRUD делается commit+refresh
    )

    log_task(
    user_id=user.id,
    task_description=task_result.explanation,
    model_name=model.name,
    credits_spent=COST_PER_PREDICT,
    difficulty=task_result.difficulty,
    vocabulary=task_result.vocabulary,
    explanation=task_result.explanation,
    is_correct=False,  #на этапе генерации ответа ещё нет, поэтому ставим False
    session=session,
)

    # 5) Сохраняем всё
    session.commit()
    session.refresh(wallet)

    logger.info("Предсказание выполнено: user_id=%s, theme_id=%s, cost=%s",
                user.id, theme.id, COST_PER_PREDICT)

    return PredictResponse(
        model_name=model.name,
        theme_name=theme.name,
        difficulty=task_result.difficulty,
        explanation=task_result.explanation,
        vocabulary=task_result.vocabulary,
        credits_spent=COST_PER_PREDICT,
        balance_after=wallet.balance,
    )


@predict_route.get(
    "/history/{user_id}",
    response_model=List[PredictionHistoryItem],
    summary="История предсказаний пользователя",
    description="Возвращает последние записи из PredictionLog"
)
def prediction_history(user_id: int, limit: int = 100, session: Session = Depends(get_session)) -> List[PredictionHistoryItem]:
    """
    История предсказаний для пользователя.
    """
    rows = get_predictions_by_user(user_id, session)
    # т.к. CRUD возвращает всё без сортировки/лимита — режем здесь
    rows = sorted(rows, key=lambda r: r.recommended_at, reverse=True)[:limit]
    logger.info("История предсказаний: user_id=%s, rows=%s", user_id, len(rows))
    return rows
