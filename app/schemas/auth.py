# app/schemas/auth.py
from typing import Literal, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, EmailStr


class Token(BaseModel):
    """Ответ при успешной авторизации (выдача access-токена)."""
    access_token: str = Field(..., description="JWT токен доступа")
    token_type: Literal["bearer"] = Field("bearer", description="Тип токена для использования в Authorization заголовке")
    expires_in: int = Field(..., description="Срок жизни access-токена в секундах")
    issued_at: datetime = Field(..., description="Время выдачи токена")


class TokenData(BaseModel):
    """Полезная нагрузка токена после декодирования."""
    user_id: int = Field(..., description="ID пользователя")
    is_admin: bool = Field(False, description="Флаг администратора")
    email: Optional[EmailStr] = Field(None, description="Email пользователя")

    model_config = ConfigDict(from_attributes=True)


class TokenPair(BaseModel):
    """Пара токенов при логине, если используешь refresh-механику."""
    access_token: str = Field(..., description="Короткоживущий JWT для доступа к API")
    refresh_token: str = Field(..., description="Долгоживущий JWT для обновления access-токена")
    token_type: Literal["bearer"] = Field("bearer", description="Тип токена")
    expires_in: int = Field(..., description="Срок жизни access-токена (в секундах)")
    issued_at: datetime = Field(..., description="Момент выдачи (UTC)")


class RefreshTokenRequest(BaseModel):
    """Запрос на обновление access-токена по refresh-токену."""
    refresh_token: str = Field(..., description="Действующий refresh-токен")
