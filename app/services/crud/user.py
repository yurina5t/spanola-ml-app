from models.user import User
from sqlmodel import Session, select
from typing import List, Optional
from sqlalchemy.orm import selectinload

def get_all_users(session: Session) -> List[User]:
    try:
        statement = (
            select(User)
            .options(
                selectinload(User.wallet),
                selectinload(User.completed_tasks)#.selectinload(TaskLog.theme)
            )
        )
        return session.exec(statement).all()
    except Exception as e:
        raise

def get_user_by_id(user_id: int, session: Session) -> Optional[User]:
    try:
        statement = select(User).where(User.id == user_id)
        return session.exec(statement).first()
    except Exception as e:
        raise

def get_user_by_email(email: str, session: Session) -> Optional[User]:
    try:
        statement = select(User).where(User.email == email)
        return session.exec(statement).first()
    except Exception as e:
        raise

def create_user(email: str, raw_password: str, session: Session) -> User:
    try:
        user = User(email=email)
        user.set_password(raw_password)
        session.add(user)
        session.commit()
        session.refresh(user)
        return user
    except Exception as e:
        session.rollback()
        raise

def delete_user(user_id: int, session: Session) -> bool:
    try:
        user = get_user_by_id(user_id, session)
        if user:
            session.delete(user)
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        raise
