# app/routers/task.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
import logging

from database.database import get_session
from models.user import User
from models.wallet import Wallet
from models.task_log import DifficultyEnum
from models.transaction_log import OperationType
from services.crud.task_log import log_task
from services.crud.transaction_log import log_transaction
from schemas.task import TaskSubmitRequest, TaskSubmitResponse

logger = logging.getLogger(__name__)
task_route = APIRouter(prefix="/tasks", tags=["tasks"])

DIFFICULTY_POINTS = {
    DifficultyEnum.easy: 1,
    DifficultyEnum.medium: 2,
    DifficultyEnum.hard: 3,
}

@task_route.post(
    "/submit",
    response_model=TaskSubmitResponse,
    status_code=status.HTTP_200_OK,
    summary="Отправить результат задания",
    description="Логирует выполнение задания и начисляет баллы за правильный ответ (atomic commit)"
)
def submit_task(req: TaskSubmitRequest, session: Session = Depends(get_session)) -> TaskSubmitResponse:
    """
    Принимаем результат выполнения задания и фиксируем всё одним commit():
    1) Лог TaskLog + TaskResult (через CRUD без коммита).
    2) Если is_correct — начисляем баллы в кошелёк и пишем TransactionLog (credit).
    3) Один общий session.commit() в конце.
    """
    # Проверяем пользователя и кошелёк
    user = session.get(User, req.user_id)
    if not user:
        logger.warning("Отправка задания: пользователь не найден, id=%s", req.user_id)
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    wallet = session.exec(select(Wallet).where(Wallet.user_id == req.user_id)).first()
    if not wallet:
        logger.warning("Отправка задания: кошелёк не найден, user_id=%s", req.user_id)
        raise HTTPException(status_code=404, detail="Кошелёк не найден")

    # 1) Логируем задачу + результат (без commit)
    log_task(
        user_id=req.user_id,
        task_description=req.task_description,
        model_name=req.model_name,
        credits_spent=0.0,
        difficulty=req.difficulty,
        vocabulary=req.vocabulary,
        explanation=req.explanation,
        is_correct=req.is_correct,
        session=session,
    )

    # 2) Начисляем баллы, если выполнено верно (без commit)
    points = DIFFICULTY_POINTS.get(req.difficulty, 0) if req.is_correct else 0
    if points > 0:
        wallet.balance += float(points)
        session.add(wallet)
        # Пишем лог транзакции (credit) без commit
        log_transaction(
            user_id=req.user_id,
            amount=float(points),
            operation=OperationType.credit.value,  # "credit"
            reason=f"Начисление за задание ({req.difficulty.value})",
            session=session,
        )
        logger.info("Начислены баллы: user_id=%s, points=%s (difficulty=%s)",
                    req.user_id, points, req.difficulty.value)

    # 3) Один общий коммит
    session.commit()
    session.refresh(wallet)

    return TaskSubmitResponse(points_awarded=points, balance_after=wallet.balance)
