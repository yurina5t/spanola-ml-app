from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Any, Optional, Literal

ModelType = Literal["comic", "grammar", "vocab"]
JobStatus = Literal["pending", "processing", "done", "failed"]

class JobCreate(BaseModel):
    user_id: int = Field(..., description="ID пользователя")
    theme_id: int = Field(..., description="ID темы")
    model_type: ModelType = Field(..., description="Тип модели: comic|grammar|vocab")

class JobOut(BaseModel):
    id: int
    user_id: int
    theme_id: int
    model_type: ModelType
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    result: Optional[Any] = None
    error: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class JobStatusOut(BaseModel):
    id: int
    status: JobStatus
    result: Optional[Any] = None
    error: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)
