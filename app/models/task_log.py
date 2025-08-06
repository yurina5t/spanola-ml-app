from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, JSON
from sqlalchemy import Enum as SqlEnum
from enum import Enum
from typing import Optional, TYPE_CHECKING, List
from datetime import datetime, timezone


if TYPE_CHECKING:
    from models.user import User
    from models.theme import Theme 

class DifficultyEnum(str, Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"

class TaskResult(SQLModel, table=True):
    """
    Результат выполнения задания (сохраняется в БД).
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    task_log_id: int = Field(foreign_key="tasklog.id", unique=True)

    difficulty: DifficultyEnum = Field(
        sa_type=SqlEnum(DifficultyEnum), 
        default=DifficultyEnum.medium
        )
    vocabulary: List[str] = Field(default_factory=list, sa_column=Column(JSON)) 
    explanation: str
    is_correct: bool = Field(default=True)

    task_log: Optional["TaskLog"] = Relationship(back_populates="result")


class TaskLog(SQLModel, table=True):
    """
    Лог завершённого задания.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    task_description: str
    model_name: str
    credits_spent: float
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    user: Optional["User"] = Relationship(back_populates="completed_tasks")
    result: Optional["TaskResult"] = Relationship(back_populates="task_log")
    theme_id: Optional[int] = Field(foreign_key="theme.id")
    theme: Optional["Theme"] = Relationship(back_populates="tasks")

