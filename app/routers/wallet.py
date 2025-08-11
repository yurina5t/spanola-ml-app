# app/routers/wallet.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from typing import Dict, List
import logging

from database.database import get_session
from services.crud.wallet import (
    get_wallet_by_user_id,
    top_up_wallet,
    admin_top_up_wallet,
    #deduct_from_wallet,
    deduct_for_reason_no_commit, 
)
from services.crud.transaction_log import get_transactions_by_user
from models.transaction_log import TransactionLog
from schemas.wallet import (
    WalletResponse,
    WalletRefillRequest,
    WalletDeductRequest,
    WalletHistoryResponse,
)

logger = logging.getLogger(__name__)
wallet_route = APIRouter(prefix="/wallet", tags=["wallet"])


@wallet_route.get(
    "/{user_id}",
    response_model=WalletResponse,
    summary="Получить баланс пользователя",
    description="Возвращает текущий баланс пользователя по его ID",
)
def get_balance(user_id: int, session: Session = Depends(get_session)) -> WalletResponse:
    """
    Вернуть текущий баланс пользователя по его ID.
    """
    wallet = get_wallet_by_user_id(user_id, session)
    if not wallet:
        logger.warning("Кошелёк не найден для пользователя id=%s", user_id)
        raise HTTPException(status_code=404, detail="Кошелёк не найден")
    logger.info("Баланс для пользователя id=%s: %s", user_id, wallet.balance)
    return WalletResponse(balance=wallet.balance)


@wallet_route.post(
    "/top_up",
    response_model=Dict[str, str],
    status_code=status.HTTP_200_OK,
    summary="Пополнить баланс пользователя",
    description="Добавляет сумму к балансу пользователя (обычное пополнение)",
)
def top_up(data: WalletRefillRequest, session: Session = Depends(get_session)) -> Dict[str, str]:
    """
    Пополнить баланс пользователя на указанную сумму.
    Примечание: причина пополнения в CRUD не логируется — лог транзакций при желании добавим позже.
    """
    try:
        top_up_wallet(data.user_id, data.amount, session)
        logger.info("Пополнение: user_id=%s, amount=%s", data.user_id, data.amount)
        return {"message": "Баланс успешно пополнен"}
    except ValueError as e:
        msg = str(e)
        code = 404 if "не найден" in msg.lower() else 400
        logger.error("Ошибка пополнения: user_id=%s, error=%s", data.user_id, msg)
        raise HTTPException(status_code=code, detail=msg)


@wallet_route.post(
    "/admin_top_up",
    response_model=Dict[str, str],
    status_code=status.HTTP_200_OK,
    summary="Админ‑пополнение баланса",
    description="Специальное пополнение администратором",
)
def admin_top_up(data: WalletRefillRequest, session: Session = Depends(get_session)) -> Dict[str, str]:
    """
    Пополнение баланса админом (обёртка над top_up_wallet).
    """
    try:
        admin_top_up_wallet(data.user_id, data.amount, session)
        logger.info("Админ‑пополнение: user_id=%s, amount=%s", data.user_id, data.amount)
        return {"message": "Баланс успешно пополнен (админ)"}
    except ValueError as e:
        msg = str(e)
        code = 404 if "не найден" in msg.lower() else 400
        logger.error("Ошибка админ‑пополнения: user_id=%s, error=%s", data.user_id, msg)
        raise HTTPException(status_code=code, detail=msg)


@wallet_route.post(
    "/spend_on_bonus",
    response_model=Dict[str, str],
    status_code=status.HTTP_200_OK,
    summary="Потратить баллы на бонусный контент",
    description="Списывает баллы при покупке бонусного комикса",
)
def spend_on_bonus(data: WalletDeductRequest, session: Session = Depends(get_session)) -> Dict[str, str]:
    """
    Списать баллы за бонусный комикс.
    1) уменьшаем баланс,
    2) пишем TransactionLog(debit, reason='bonus_purchase'),
    3) один общий commit().
    """
    try:
        deduct_for_reason_no_commit(
            user_id=data.user_id,
            amount=data.amount,
            reason="bonus_purchase",
            session=session,
        )
        session.commit()
        logger.info("Списание (бонус): user_id=%s, amount=%s", data.user_id, data.amount)
        return {"message": "Бонус успешно куплен, баллы списаны"}
    except ValueError as e:
        session.rollback()
        msg = str(e)
        if "не найден" in msg.lower():
            code = 404
        elif "недостаточно" in msg.lower():
            code = 409
        else:
            code = 400
        logger.error("Ошибка списания (бонус): user_id=%s, error=%s", data.user_id, msg)
        raise HTTPException(status_code=code, detail=msg)
    except Exception as e:
        session.rollback()
        logger.error("Неожиданная ошибка списания (бонус): user_id=%s, error=%s", data.user_id, str(e))
        raise HTTPException(status_code=500, detail="Ошибка при списании баллов")


@wallet_route.get(
    "/can_spend/{user_id}/{amount}",
    response_model=Dict[str, bool],
    summary="Проверка достаточности баллов",
    description="Возвращает, хватает ли баллов на операцию",
)
def can_spend(user_id: int, amount: float, session: Session = Depends(get_session)) -> Dict[str, bool]:
    """
    Проверить, хватает ли баллов на операцию списания.
    """
    wallet = get_wallet_by_user_id(user_id, session)
    if not wallet:
        logger.warning("Проверка can_spend: кошелёк не найден, user_id=%s", user_id)
        raise HTTPException(status_code=404, detail="Кошелёк не найден")
    can = wallet.balance >= amount
    logger.info("Проверка can_spend: user_id=%s, amount=%s, can=%s", user_id, amount, can)
    return {"can_spend": can}


@wallet_route.get(
    "/history/{user_id}",
    response_model=List[WalletHistoryResponse],
    summary="История операций по кошельку",
    description="Показывает последние транзакции пользователя (credit/debit)",
)
def wallet_history(user_id: int, limit: int = 100, session: Session = Depends(get_session)) -> List[WalletHistoryResponse]:
    """
    Вернуть последние транзакции пользователя из лога TransactionLog.
    """
    rows = get_transactions_by_user(user_id, session)
    rows = sorted(rows, key=lambda r: r.timestamp, reverse=True)[:limit]
    logger.info("История кошелька: user_id=%s, rows=%s", user_id, len(rows))
    return [WalletHistoryResponse.from_orm(x) for x in rows]
