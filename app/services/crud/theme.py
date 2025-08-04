from sqlmodel import Session, select
from models.theme import Theme
from typing import List, Optional


def get_all_themes(session: Session) -> List[Theme]:
    """
    Получить список всех тем.
    """
    statement = select(Theme).order_by(Theme.level, Theme.name)
    return session.exec(statement).all()


def get_theme_by_id(theme_id: int, session: Session) -> Optional[Theme]:
    """
    Получить тему по ID.
    """
    statement = select(Theme).where(Theme.id == theme_id)
    return session.exec(statement).first()


def get_theme_by_name(name: str, session: Session) -> Optional[Theme]:
    """
    Получить тему по названию.
    """
    statement = select(Theme).where(Theme.name == name)
    return session.exec(statement).first()


def create_theme(theme: Theme, session: Session) -> Theme:
    """
    Создать новую тему.
    """
    session.add(theme)
    session.commit()
    session.refresh(theme)
    return theme


def delete_theme(theme_id: int, session: Session) -> bool:
    """
    Удалить тему по ID.
    """
    theme = get_theme_by_id(theme_id, session)
    if not theme:
        return False
    session.delete(theme)
    session.commit()
    return True

def get_themes_by_level(level: str, session: Session) -> List[Theme]:
    """
    Получить все темы заданного уровня (A1, A2, B1 и т.д.).
    """
    statement = select(Theme).where(Theme.level == level).order_by(Theme.name)
    return session.exec(statement).all()

from sqlalchemy.orm import selectinload

def get_theme_with_tasks(theme_id: int, session: Session) -> Optional[Theme]:
    """
    Получить тему по ID вместе с привязанными заданиями.
    """
    statement = (
        select(Theme)
        .where(Theme.id == theme_id)
        .options(selectinload(Theme.tasks))
    )
    return session.exec(statement).first()
