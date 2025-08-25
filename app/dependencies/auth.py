# app/dependencies/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session

from core.security import decode_access_token
from database.database import get_session
from services.crud.user import get_user_by_id
from schemas.auth import TokenData

bearer_scheme = HTTPBearer(auto_error=False)


def _extract_bearer_token(
    credentials: HTTPAuthorizationCredentials | None,
) -> str:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется аутентификация (Bearer токен)",
        )
    return credentials.credentials


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    session: Session = Depends(get_session),
) -> TokenData:
    """
    Достаёт и валидирует Bearer-токен, проверяет, что пользователь существует.
    Возвращает TokenData (user_id, is_admin, email).
    """
    token = _extract_bearer_token(credentials)
    payload = decode_access_token(token)

    user_id = payload.get("user_id")
    is_admin = payload.get("is_admin", False)
    email = payload.get("email")

    if not isinstance(user_id, int):
        raise HTTPException(status_code=401, detail="Некорректный payload токена")

    user = get_user_by_id(user_id, session)
    if not user:
        raise HTTPException(status_code=401, detail="Пользователь не найден")

    return TokenData(user_id=user_id, is_admin=bool(is_admin), email=email)


def get_current_admin(
    token_data: TokenData = Depends(get_current_user),
) -> TokenData:
    """
    Требует роль администратора.
    """
    if not token_data.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуются права администратора",
        )
    return token_data
