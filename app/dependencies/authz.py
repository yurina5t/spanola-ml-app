# app/dependencies/authz.py
from fastapi import HTTPException, status, Depends
from .auth import TokenData, get_current_user

def self_or_admin(
    user_id: int,
    token: TokenData = Depends(get_current_user)
) -> TokenData:
    """
    Разрешает доступ если:
    - пользователь админ, ИЛИ
    - user_id в пути равен user_id из токена.
    Возвращает TokenData (можно использовать дальше в обработчике).
    """
    if token.is_admin or token.user_id == user_id:
        return token
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Доступ запрещён")
