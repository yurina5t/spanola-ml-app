# app/routers/theme.py
from fastapi import APIRouter, HTTPException, Depends, status
from sqlmodel import Session
from typing import List, Dict
import logging

from database.database import get_session
from services.crud import theme as ThemeService
from models.theme import Theme
from schemas.theme import ThemeCreate, ThemeResponse

logger = logging.getLogger(__name__)
theme_route = APIRouter(prefix="/themes", tags=["themes"])

@theme_route.get(
        "/", 
        response_model=List[ThemeResponse], 
        summary="Список тем",
        description="Вернуть все доступные темы."
    )
def list_themes(session: Session = Depends(get_session)) -> List[ThemeResponse]:
    rows = ThemeService.get_all_themes(session)
    logger.info("Тем загружено: %d", len(rows))
    return rows

@theme_route.get(
        "/level/{level}",
        response_model=List[ThemeResponse], 
        summary="Темы по уровню"
        )
def get_themes_by_level(level: str, session: Session = Depends(get_session)) -> List[ThemeResponse]:
    rows = ThemeService.get_themes_by_level(level, session)
    logger.info("Тем уровня %s: %d", level, len(rows))
    return rows

@theme_route.get(
        "/{theme_id}",
        response_model=ThemeResponse, 
        summary="Получить тему по ID",
        description="Вернуть тему по её ID. Если тема не найдена, вернёт 404."
    )
def get_theme(theme_id: int, session: Session = Depends(get_session)) -> ThemeResponse:
    t = ThemeService.get_theme_by_id(theme_id, session)
    if not t:
        logger.warning("Тема не найдена: id=%s", theme_id)
        raise HTTPException(status_code=404, detail="Тема не найдена")
    return t

@theme_route.post(
        "/", 
        response_model=ThemeResponse, 
        status_code=status.HTTP_201_CREATED, 
        summary="Создать тему"
    )
def create_theme(data: ThemeCreate, session: Session = Depends(get_session)) -> ThemeResponse:
    try:    
        theme = Theme(
            name=data.name, 
            level=data.level, 
            base_comic=data.base_comic,
            bonus_comics=data.bonus_comics,
        )
        theme = ThemeService.create_theme(theme, session)
        logger.info("Создана тема: id=%s, name=%s", theme.id, theme.name)
        return theme
    except Exception as e:
        logger.error("Ошибка создания темы: %s", e)
        raise HTTPException(status_code=400, detail="Не удалось создать тему")

@theme_route.delete(
        "/{theme_id}", 
        response_model=Dict[str, str], 
        summary="Удалить тему"
    )
def delete_theme(theme_id: int, session: Session = Depends(get_session)) -> Dict[str, str]:
    ok = ThemeService.delete_theme(theme_id, session)
    if not ok:
        logger.warning("Удаление темы — не найдена: id=%s", theme_id)
        raise HTTPException(status_code=404, detail="Тема не найдена")
    logger.info("Тема удалена: id=%s", theme_id)
    return {"message": "Тема удалена", "theme_id": str(theme_id)}
