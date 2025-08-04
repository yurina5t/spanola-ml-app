from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime, timezone

if TYPE_CHECKING:
    from models.user import User

class TransactionLog(SQLModel, table=True):
    """
    Лог операций с баллами пользователя (credit / debit).
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    amount: float
    operation: str  # 'credit' или 'debit'
    reason: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    user: Optional["User"] = Relationship(back_populates="transactions")
