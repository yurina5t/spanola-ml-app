from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime
from models.task_log import DifficultyEnum

class TaskResultOut(BaseModel):
    difficulty: DifficultyEnum = Field(..., description="Уровень сложности задания")
    vocabulary: List[str] = Field(..., description="Список словарных единиц")
    explanation: str = Field(..., description="Пояснение/инструкция к заданию")
    is_correct: bool = Field(..., description="Правильно ли выполнено задание")
    model_config = ConfigDict(from_attributes=True)

class TaskLogItem(BaseModel):
    id: int = Field(..., description="ID лога задания")
    user_id: int = Field(..., description="ID пользователя")
    timestamp: datetime = Field(..., description="Когда зафиксирован лог")
    task_description: str = Field(..., description="Короткое описание/промпт задания")
    model_name: str = Field(..., description="Имя модели")
    credits_spent: float = Field(..., description="Сколько кредитов списано")
    result: Optional[TaskResultOut] = Field(None, description="Результат выполнения (если есть)")
    
    model_config = ConfigDict(from_attributes=True)
