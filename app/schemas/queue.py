from pydantic import BaseModel, Field, ConfigDict
from typing import Literal
from datetime import datetime
from uuid import UUID, uuid4

TaskKind = Literal["comic", "grammar", "vocab"]

class MLTaskMessage(BaseModel):
    task_id: UUID = Field(default_factory=uuid4, description="ID задачи (для трассировки)")
    user_id: int
    theme_id: int
    model: TaskKind
    is_bonus: bool = False
    cost: float = 1.0
    created_at: datetime = Field(default_factory=datetime.utcnow)

class MLResultMessage(BaseModel):
    task_id: UUID
    user_id: int
    theme_id: int
    model: TaskKind
    ok: bool
    error: str | None = None

    # полезно, если захочешь отдельную очередь результатов
    model_config = ConfigDict(from_attributes=True)
