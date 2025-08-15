from pydantic import BaseModel, Field
from typing import Optional

class ActionMessage(BaseModel):
    message: str = Field(..., description="Статусное сообщение операции")
    user_id: Optional[int] = Field(None, description="ID пользователя, над которым выполнено действие")
