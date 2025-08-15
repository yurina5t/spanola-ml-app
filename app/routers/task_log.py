from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from typing import List
import logging

from database.database import get_session
from services.crud.task_log import get_tasks_by_user, get_task_by_id
from schemas.task_log import TaskLogItem
from dependencies.auth import TokenData
from dependencies.authz import self_or_admin

logger = logging.getLogger(__name__)
tasklog_route = APIRouter(prefix="/tasks", tags=["tasks"])

@tasklog_route.get(
        "/history/{user_id}", 
        response_model=List[TaskLogItem],
        summary="История задач пользователя",
    )
def tasks_history(
    user_id: int, 
    limit: int = 100, 
    session: Session = Depends(get_session),
    _: TokenData = Depends(self_or_admin),
) -> List[TaskLogItem]:
    """
    Вернуть последние логи задач пользователя.
    """
    rows = get_tasks_by_user(user_id, session)
    rows = sorted(rows, key=lambda r: r.timestamp, reverse=True)[:limit]
    logger.info("История задач: user_id=%s, rows=%s", user_id, len(rows))
    return [TaskLogItem.model_validate(r) for r in rows]

@tasklog_route.get(
        "/{task_id}", 
        response_model=TaskLogItem, 
        summary="Детали лога задачи",
    )
def task_detail(task_id: int, session: Session = Depends(get_session)) -> TaskLogItem:
    """
    Вернуть подробности по конкретному логу задачи.
    """
    row = get_task_by_id(task_id, session)
    if not row:
        logger.warning("Лог задачи не найден: id=%s", task_id)
        raise HTTPException(status_code=404, detail="Лог задачи не найден")
    return TaskLogItem.model_validate(row)
