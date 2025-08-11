from pydantic import BaseModel, Field

class ActionMessage(BaseModel):
    message: str = Field(..., description="Статусное сообщение операции")
