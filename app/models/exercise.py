# app/models/exercise.py
from typing import Optional
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field

class Exercise(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    theme_id: int = Field(index=True, foreign_key="theme.id")
    level: str
    difficulty: str
    payload_json: str  # здесь лежат вопросы С правильными ответами
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
