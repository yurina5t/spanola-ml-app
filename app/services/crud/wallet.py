from sqlmodel import Session, select
from models.wallet import Wallet
from models.transaction_log import OperationType
from services.crud.transaction_log import log_transaction
from typing import Optional

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
    if amount <= 0:
        raise ValueError("Сумма пополнения должна быть > 0")
    
    wallet = get_wallet_by_user_id(user_id, session)
    if not wallet:
        raise ValueError("Кошелёк не найден")

    wallet.add(amount)
    session.add(wallet)
    # создаём лог внутри той же транзакции
    log_transaction(
        user_id=user_id,
        amount=amount,
        operation=OperationType.credit.value,
        reason="Пополнение баланса",
        session=session,
    )
    session.commit() # единый коммит для баланса и лога
    session.refresh(wallet)
    return wallet

def credit_for_reason_no_commit(user_id: int, amount: float, reason: str, session: Session) -> None:
    """
    Начислить баллы БЕЗ commit(). Делает:
      - проверку кошелька и увеличение баланса
      - пишет лог транзакции (credit) через log_transaction()
    Коммит выполняет вызывающая сторона.
    """
    if amount <= 0:
        raise ValueError("Сумма начисления должна быть > 0")
    
    wallet = get_wallet_by_user_id(user_id, session)
    if not wallet:
        raise ValueError("Кошелёк не найден")

    wallet.add(amount)
    session.add(wallet)
    log_transaction(
        user_id=user_id,
        amount=amount,
        operation=OperationType.credit.value,  # "credit"
        reason=reason,
        session=session,
    )

def admin_top_up_wallet(user_id: int, amount: float, session: Session) -> Wallet:
    """
    Специальное пополнение админом (можно вести логи).
    """
    return top_up_wallet(user_id, amount, session)


def deduct_from_wallet(user_id: int, amount: float, session: Session) -> bool:
    """
    Списать баллы (например, за бонусный комикс).
    """
    if amount <= 0:
        raise ValueError("Сумма списания должна быть > 0")
    
    wallet = get_wallet_by_user_id(user_id, session)
    if not wallet:
        raise ValueError("Кошелёк не найден")

    if not wallet.deduct(amount):
        raise ValueError("Недостаточно баллов")
        
    session.add(wallet)
    log_transaction(
        user_id=user_id,
        amount=amount,
        operation=OperationType.debit.value,
        reason="Списание за бонусный комикс",
        session=session,
    )
    session.commit()
    return True

def deduct_for_reason_no_commit(user_id: int, amount: float, reason: str, session: Session) -> None:
    """
    Списать баллы БЕЗ commit(). Делает:
      - проверку кошелька и баланса
      - уменьшает баланс
      - пишет лог транзакции (debit) через log_transaction()
    Коммит выполняет вызывающая сторона.
    """
    if amount <= 0:
        raise ValueError("Сумма списания должна быть > 0")
    
    wallet = get_wallet_by_user_id(user_id, session)
    if not wallet:
        raise ValueError("Кошелёк не найден")

    if not wallet.deduct(amount):
        raise ValueError("Недостаточно баллов")

    session.add(wallet)
    log_transaction(
        user_id=user_id,
        amount=amount,
        operation=OperationType.debit.value,  # "debit"
        reason=reason,
        session=session,
    )
