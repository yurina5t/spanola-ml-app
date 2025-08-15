from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime, timezone
import re
from hashlib import sha256
import bcrypt

if TYPE_CHECKING:
    from models.task_log import TaskLog
    from models.transaction_log import TransactionLog
    from models.prediction_log import PredictionLog
    from models.wallet import Wallet


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(..., unique=True, index=True, min_length=5, max_length=255)
    password: str= Field(..., min_length=8)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_admin: bool = Field(default=False)
    
    wallet: Optional["Wallet"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"})

    completed_tasks: List["TaskLog"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    transactions: List["TransactionLog"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    predictions: List["PredictionLog"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )    


    def set_password(self, raw_password: str):
        self._validate_password(raw_password)
        hashed = bcrypt.hashpw(raw_password.encode(), bcrypt.gensalt())
        self.password = hashed.decode("utf-8")

    def check_password(self, raw_password: str) -> bool:
        return bcrypt.checkpw(raw_password.encode(), self.password.encode("utf-8"))

    def _validate_email(self):
        pattern = re.compile(r'^[\w\.-]+@[\w\.-]+\.\w+$')
        if not pattern.match(self.email):
            raise ValueError("Неверный формат email")
        return True

    def _validate_password(self, raw_password: str):
        if len(raw_password) < 8:
            raise ValueError("Пароль должен содержать не менее 8 символов")

    def __str__(self):
        return f"User(id={self.id}, email={self.email})"

    class Config:
        validate_assignment = True
        arbitrary_types_allowed = True
