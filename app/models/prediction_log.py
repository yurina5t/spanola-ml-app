from sqlmodel import SQLModel, Field
from typing import Optional, TYPE_CHECKING
from datetime import datetime, timezone


class PredictionLog(SQLModel, table=True):
    """
    Лог предсказаний модели для пользователя.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int
    model_name: str
    theme_name: str
    difficulty: str
    recommended_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
