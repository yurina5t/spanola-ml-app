from fastapi import APIRouter, HTTPException, status, Depends
from sqlmodel import Session
from typing import List, Dict
import logging
from sqlalchemy.exc import IntegrityError

from database.database import get_session
from services.crud import user as UserService
from services.crud.wallet import create_wallet_for_user
from schemas.user import UserCreate, UserLogin, UserResponse
from schemas.auth import Token
from schemas.common import ActionMessage
from core.security import create_access_token
from dependencies.auth import get_current_admin, TokenData
from dependencies.authz import self_or_admin

logger = logging.getLogger(__name__)

user_route = APIRouter(prefix="/users", tags=["users"])


@user_route.post(
    '/signup',
    response_model=Dict[str, str],
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация пользователя",
    description="Создание нового пользователя + автоматическое создание кошелька"
)
async def signup(data: UserCreate, session: Session = Depends(get_session)) -> Dict[str, str]:
    """
    Регистрация:
    1) Проверяем уникальность email.
    2) Создаём пользователя через CRUD (он хэширует пароль).
    3) Создаём кошелёк с балансом 0.
    """
    try:
        if UserService.get_user_by_email(data.email, session):
            logger.warning("Регистрация отклонена — email уже существует: %s", data.email)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Пользователь с таким email уже существует"
            )
        user=UserService.create_user(
            email=data.email,
            raw_password=data.password, 
            session=session)
        logger.info("Пользователь успешно зарегистрирован: %s (id=%s)", data.email, user.id)
        
        # Автоматически создаём кошелёк для нового пользователя
        create_wallet_for_user(user.id, session)
        logger.info("Кошелёк создан для пользователя: %s (id=%s)", data.email, user.id)

        return {"message": "Пользователь успешно зарегистрирован и кошелёк создан", "user_id": user.id}

    except IntegrityError:
        session.rollback()
        logger.warning("Регистрация столкнулась с дублирующимся email (IntegrityError): %s", data.email)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Пользователь с таким email уже существует"
            )
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error("Ошибка при регистрации пользователя %s: %s", data.email, str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Ошибка при регистрации пользователя"
            )


@user_route.post(
    '/signin',
    response_model=Token,
    summary="Авторизация",
    description="Авторизация пользователя по email и паролю. Возвращает Bearer токен.",
)
async def signin(data: UserLogin, session: Session = Depends(get_session)) -> Token:
    """
    Авторизация пользователя.
    """
    user = UserService.get_user_by_email(data.email, session)
    if not user:
        logger.warning("Попытка входа с несуществующим email: %s", data.email)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Пользователь не найден",
            )

    if not user.check_password(data.password):
        logger.warning("Неуспешная авторизация (неверный пароль): %s", data.email)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Неверные учетные данные"
            )
    # формируем payload и выпускаем токен
    payload = {"user_id": int(user.id), "is_admin": bool(user.is_admin), "email": user.email}
    token, expires_in, issued_at = create_access_token(payload)

    logger.info("Успешная авторизация: %s", data.email)
    return Token(access_token=token, token_type="bearer", expires_in=expires_in, issued_at=issued_at)


@user_route.get(
    "/",
    response_model=List[UserResponse],
    summary="Список пользователей",
    response_description="Возвращает список всех пользователей",
)
async def get_all_users(
        session: Session = Depends(get_session),
        _: TokenData = Depends(get_current_admin),
    ) -> List[UserResponse]:
    """
    Получение списка всех пользователей.
    Возвращаем только публичные поля (через схему UserResponse),
    чтобы не утекли пароли.
    """
    try:
        users = UserService.get_all_users(session)
        logger.info("Получено пользователей: %d", len(users))
        return [UserResponse.model_validate(u) for u in users]
    except Exception as e:
        logger.error("Ошибка при получении пользователей: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении пользователей",
            )

@user_route.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Получить пользователя по ID",
)
async def get_user(
    user_id: int, 
    session: Session = Depends(get_session), 
    _: TokenData = Depends(self_or_admin),
) -> UserResponse:
    """
    Вернуть публичные данные пользователя по его ID.
    """
    user = UserService.get_user_by_id(user_id, session)
    if not user:
        logger.warning("Пользователь не найден: id=%s", user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Пользователь не найден",
            )
    logger.info("Пользователь получен: id=%s", user_id)
    return UserResponse.model_validate(user)


@user_route.delete(
    "/{user_id}",
    response_model=ActionMessage,
    summary="Удалить пользователя",
)
async def delete_user(
    user_id: int, 
    session: Session = Depends(get_session),
    _: TokenData = Depends(get_current_admin),
) -> ActionMessage:
    """
    Удалить пользователя по ID.
    """
    try:
        ok = UserService.delete_user(user_id, session)
        if not ok:
            logger.warning("Удаление пользователя — не найден: id=%s", user_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Пользователь не найден"
            )
        logger.info("Пользователь удалён: id=%s", user_id)
        return ActionMessage(message="Пользователь удалён", user_id=user_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Ошибка при удалении пользователя id=%s: %s", user_id, str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при удалении пользователя"
        )