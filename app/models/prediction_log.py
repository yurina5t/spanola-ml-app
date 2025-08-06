from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime, timezone

if TYPE_CHECKING:
    from models.user import User

class PredictionLog(SQLModel, table=True):
    """
    Лог предсказаний модели для пользователя.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    model_name: str
    theme_name: str
    difficulty: str
    recommended_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    user: Optional["User"] = Relationship(back_populates="predictions")
