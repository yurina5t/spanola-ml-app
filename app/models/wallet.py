from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from models.user import User

class Wallet(SQLModel, table=True):
    """
    Кошелёк пользователя — управляет только балансом.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True)
    balance: float = Field(default=0.0)

    user: Optional["User"] = Relationship(back_populates="wallet")


    def add(self, amount: float):
        self.balance += amount

    def deduct(self, amount: float) -> bool:
        if self.balance >= amount:
            self.balance -= amount
            return True
        return False
    