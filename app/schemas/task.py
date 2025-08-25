from pydantic import BaseModel, Field, ConfigDict
from typing import List
from models.task_log import DifficultyEnum  # используем тот же Enum, что в моделях

class TaskSubmitRequest(BaseModel):
    user_id: int = Field(..., description="ID пользователя")
    model_name: str = Field(..., description="Имя модели, выдавшей задание")
    task_description: str = Field(..., description="Короткое описание/промпт задания")
    difficulty: DifficultyEnum = Field(..., description="Сложность задания (easy/medium/hard)")
    vocabulary: List[str] = Field(default_factory=list, description="Словарные единицы из задания")
    explanation: str = Field(..., description="Пояснение/инструкция к заданию")
    is_correct: bool = Field(..., description="Верно ли выполнено задание")

class TaskSubmitResponse(BaseModel):
    points_awarded: int = Field(..., description="Сколько баллов начислено за задание")
    balance_after: float = Field(..., description="Баланс пользователя после начисления")
    model_config = ConfigDict(from_attributes=True)
