from sqlmodel import Session, select
from models.user import User
from models.transaction_log import TransactionLog
from models.task_log import TaskLog
from typing import List


def top_up_user(user: User, amount: float, session: Session, reason: str = "Пополнение администратором"):
    """
    Пополнение баланса пользователю администратором.
    """
    user.wallet.balance += amount

    transaction = TransactionLog(
        user_id=user.id,
        amount=amount,
        operation="credit",
        reason=reason
    )
    session.add(transaction)
    session.commit()
    session.refresh(user.wallet)


def view_all_task_logs(session: Session) -> list[TaskLog]:
    """
    Получить все логи заданий всех пользователей.
    """
    statement = select(TaskLog)
    return session.exec(statement).all()


def get_transaction_history_for_user(user_id: int, session: Session) -> List[TransactionLog]:
    """
    Получить все транзакции конкретного пользователя (админская функция).
    """
    statement = select(TransactionLog).where(TransactionLog.user_id == user_id).order_by(TransactionLog.timestamp.desc())
    return session.exec(statement).all()
