from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

class WalletResponse(BaseModel):
    balance: float = Field(..., ge=0, description="Текущий баланс пользователя")
    model_config = ConfigDict(from_attributes=True)


class WalletRefillRequest(BaseModel):
    user_id: int = Field(..., description="ID пользователя")
    amount: float = Field(..., gt=0, description="Сумма пополнения")
    reason: Optional[str] = Field(default="Пополнение", description="Причина пополнения")


class WalletDeductRequest(BaseModel):
    user_id: int = Field(..., description="ID пользователя")
    amount: float = Field(..., gt=0, description="Сумма списания")
    reason: Optional[str] = Field(default="Списание", description="Причина списания")


class WalletHistoryResponse(BaseModel):
    operation: str = Field(..., description="Тип операции: credit/debit")
    amount: float = Field(..., description="Сумма операции")
    reason: str = Field(..., description="Причина")
    timestamp: datetime = Field(..., description="Дата и время операции")
    model_config = ConfigDict(from_attributes=True)