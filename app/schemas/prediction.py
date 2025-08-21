from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import List

class PredictRequest(BaseModel):
    user_id: int = Field(..., description="ID пользователя (пока без JWT)")
    theme_id: int = Field(..., description="ID темы (Theme)")
    is_bonus: bool = Field(False, description="Сгенерировать бонусный комикс")

class PredictResponse(BaseModel):
    model_name: str = Field(..., description="Имя модели генерации")
    theme_name: str = Field(..., description="Название темы")
    difficulty: str = Field(..., description="Уровень сложности задания")
    explanation: str = Field(..., description="Пояснение/инструкция к заданию")
    vocabulary: List[str] = Field(..., description="Список словарных единиц")
    credits_spent: float = Field(..., description="Списанные кредиты за запрос")
    balance_after: float = Field(..., description="Баланс пользователя после списания")

class PredictionHistoryItem(BaseModel):
    model_name: str = Field(..., description="Имя модели генерации")
    theme_name: str = Field(..., description="Название темы")
    difficulty: str = Field(..., description="Уровень сложности задания")
    recommended_at: datetime = Field(..., description="Время рекомендации/генерации")

    model_config = ConfigDict(from_attributes=True)
