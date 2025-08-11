# app/schemas/theme.py
from pydantic import BaseModel, ConfigDict, Field
from typing import List

class ThemeCreate(BaseModel):
    name: str = Field(..., description="Название темы")
    level: str = Field(..., description="Уровень (A1, A2, ...)")
    base_comic: str = Field(..., min_length=1, description="Файл базового комикса")             
    bonus_comics: List[str] = Field(default_factory=list, description="Список бонусных комиксов")

class ThemeResponse(BaseModel):
    id: int = Field(..., description="ID темы")
    name: str = Field(..., description="Название темы")
    level: str = Field(..., description="Уровень (A1, A2, ...)")
    base_comic: str = Field(..., description="Базовый комикс")
    bonus_comics: List[str] = Field(default_factory=list, description="Бонусные комиксы")
    description: str | None = Field(None, description="Описание темы")
    model_config = ConfigDict(from_attributes=True)

