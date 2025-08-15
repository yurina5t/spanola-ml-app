# app/core/security.py
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Tuple

import jwt  
from fastapi import HTTPException, status

from database.config import get_settings

settings = get_settings()

SECRET_KEY: str = settings.SECRET_KEY
ALGORITHM: str = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(settings.ACCESS_TOKEN_EXPIRE_MINUTES)


def create_access_token(payload: Dict[str, Any]) -> Tuple[str, int, datetime]:
    """
    Сгенерировать access-токен (JWT).
    Возвращает кортеж: (token, expires_in_sec, issued_at_utc).
    """
    issued_at = datetime.now(timezone.utc)
    expire = issued_at + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {**payload, "iat": int(issued_at.timestamp()), "exp": int(expire.timestamp())}
    try:
        token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка генерации токена: {e}",
        )

    expires_in = int((expire - issued_at).total_seconds())
    return token, expires_in, issued_at


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Декодировать/проверить токен. Бросает HTTPException при ошибке.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Токен истёк")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Недействительный токен")

