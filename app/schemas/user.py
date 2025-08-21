from pydantic import BaseModel, EmailStr, ConfigDict, Field, StringConstraints
from typing import Annotated
from datetime import datetime


class UserCreate(BaseModel):
    email: EmailStr = Field(..., description="Электронная почта пользователя")
    password: Annotated[
        str, 
        StringConstraints(min_length=8)
    ] = Field(..., description="Пароль (не менее 8 символов)")


class UserLogin(BaseModel):
    email: EmailStr = Field(..., description="Электронная почта пользователя")
    password: str = Field(..., description="Пароль пользователя")


class UserResponse(BaseModel):
    id: int = Field(..., description="ID пользователя")
    email: EmailStr = Field(..., description="Электронная почта пользователя")
    created_at: datetime = Field(..., description="Дата и время регистрации")
    is_admin: bool = Field(..., description="Признак администратора")

    model_config = ConfigDict(from_attributes=True)

class SignupOut(BaseModel):
    message: str
    user_id: int