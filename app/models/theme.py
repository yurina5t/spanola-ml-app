from typing import List, Optional
from typing import TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, JSON

if TYPE_CHECKING:
    from models.task_log import TaskLog

class Theme(SQLModel, table=True):
    """
    Тематический модуль.
    Включает название темы, уровень сложности (A1, A2 и т.д.), базовый и бонусные комиксы.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    level: str
    base_comic: str
    bonus_comics: List[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    tasks: List["TaskLog"] = Relationship(back_populates="theme")
    description: str | None = Field(default=None, description="Описание темы")

    def get_bonus_comic(self) -> Optional[str]:
        """Возвращает доступный бонусный комикс или None."""
        return self.bonus_comics[0] if self.bonus_comics else None