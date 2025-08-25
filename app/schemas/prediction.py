from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import List, Optional

# --- базовые схемы предсказаний ---
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

# --- ПАНЕЛЬ УПРАЖНЕНИЙ ---

class ExerciseItem(BaseModel):
    prompt: str
    choices: List[str] = Field(default_factory=list)
    answer: Optional[str] = None
    is_bonus: bool = False

class PanelRequest(BaseModel):
    user_id: int = Field(..., gt=0)
    theme_id: int = Field(..., gt=0)
    count: int = Field(15, ge=1, le=50, description="Сколько базовых упражнений сгенерировать")
    is_bonus: bool = Field(False, description="Если True — спишем 1 кредит и добавим 1 бонус-задачу")

class PanelResponse(BaseModel):
    theme_name: str
    count: int
    exercises: List[ExerciseItem] = Field(default_factory=list)
    bonus_included: bool
    credits_spent: float = Field(0, ge=0)
    balance_after: float = Field(..., ge=0)