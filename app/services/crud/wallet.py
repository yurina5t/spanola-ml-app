from sqlmodel import Session, select
from models.wallet import Wallet
from models.transaction_log import TransactionLog
from typing import Optional
from datetime import datetime, timezone

def get_wallet_by_user_id(user_id: int, session: Session) -> Optional[Wallet]:
    """
    Получить кошелёк по ID пользователя.
    """
    statement = select(Wallet).where(Wallet.user_id == user_id)
    return session.exec(statement).first()


def create_wallet_for_user(user_id: int, session: Session) -> Wallet:
    """
    Создать кошелёк для нового пользователя.
    """
    wallet = Wallet(user_id=user_id, balance=0.0)
    session.add(wallet)
    session.commit()
    session.refresh(wallet)
    return wallet

def top_up_wallet(user_id: int, amount: float, session: Session) -> Wallet:
    """
    Пополнить кошелёк баллами (за задания, бонусы и т.п.).
    """
    wallet = get_wallet_by_user_id(user_id, session)
    if not wallet:
        raise ValueError("Кошелёк не найден")

    wallet.add(amount)
    session.add(wallet)
    session.commit()
    session.refresh(wallet)
    return wallet


def admin_top_up_wallet(user_id: int, amount: float, session: Session) -> Wallet:
    """
    Специальное пополнение админом (можно вести логи).
    """
    return top_up_wallet(user_id, amount, session)


def deduct_from_wallet(user_id: int, amount: float, session: Session) -> bool:
    """
    Списать баллы (например, за бонусный комикс).
    """
    wallet = get_wallet_by_user_id(user_id, session)
    if not wallet:
        raise ValueError("Кошелёк не найден")

    if not wallet.deduct(amount):
        raise ValueError("Недостаточно баллов")
    
    # Лог транзакции
    log = TransactionLog(
        user_id=user_id,
        amount=amount,
        operation="debit",
        reason="Списание за бонусный комикс",
        timestamp=datetime.now(timezone.utc)
    )
    
    session.add_all([wallet, log])
    session.commit()
    return True
