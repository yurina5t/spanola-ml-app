from sqlmodel import Session, select
from models.transaction_log import TransactionLog
from typing import List

def log_transaction(user_id: int, amount: float, operation: str, reason: str, session: Session) -> TransactionLog:
    """
    Сохранить лог транзакции (credit/debit).

    Args:
        user_id (int): ID пользователя
        amount (float): сумма операции
        operation (str): тип — 'credit' или 'debit'
        reason (str): причина операции
        session (Session): SQLModel-сессия

    Returns:
        TransactionLog: созданный лог
    """
    log = TransactionLog(
        user_id=user_id,
        amount=amount,
        operation=operation,
        reason=reason
    )
    session.add(log)
    # убираем commit и refresh, теперь это делает вызывающая функция
    return log

def get_transactions_by_user(user_id: int, session: Session) -> List[TransactionLog]:
    """
    Возвращает все транзакции пользователя.

    Args:
        user_id (int): ID пользователя
        session (Session): SQLModel-сессия

    Returns:
        List[TransactionLog]: список транзакций
    """
    statement = select(TransactionLog).where(TransactionLog.user_id == user_id)
    return session.exec(statement).all()
