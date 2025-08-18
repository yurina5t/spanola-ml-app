from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from typing import List
from database.database import get_session
from dependencies.auth import get_current_user, TokenData
from dependencies.authz import self_or_admin
from services.crud.job import create_job, get_job, list_jobs_by_user
from schemas.job import JobCreate, JobOut, JobStatusOut
from mq.publisher import publish_task
from services.crud.wallet import deduct_from_wallet

predict_async_route = APIRouter(prefix="/predictions", tags=["predictions-async"])

COST_PER_PREDICT = 1.0

@predict_async_route.post(
    "/async",
    response_model=JobOut,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Создать асинхронную ML-задачу",
    description="Генерация бесплатна; списание кредитов — только если is_bonus=true",
)
def create_async_job(
    data: JobCreate,
    session: Session = Depends(get_session),
    token: TokenData = Depends(get_current_user),
) -> JobOut:
    # доступ: self или admin
    if not (token.is_admin or token.user_id == data.user_id):
        raise HTTPException(status_code=403, detail="Можно запускать задачи только для себя")

    # списываем кредит если бонус (если недостаточно — поднимет ValueError -> 409)
    if data.is_bonus:
        deduct_from_wallet(user_id=data.user_id, amount=COST_PER_PREDICT, session=session)

    # создаём запись и публикуем сообщение
    job = create_job(user_id=data.user_id, theme_id=data.theme_id, model_type=data.model_type, session=session)
    publish_task(queue_name=f"queue.{data.model_type}", message={"job_id": job.id})
    return job

@predict_async_route.get(
    "/jobs/{job_id}",
    response_model=JobStatusOut,
    summary="Статус задачи"
)
def job_status(
    job_id: int,
    session: Session = Depends(get_session),
    token: TokenData = Depends(get_current_user),
) -> JobStatusOut:
    job = get_job(job_id, session)
    if not job:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    if not (token.is_admin or token.user_id == job.user_id):
        raise HTTPException(status_code=403, detail="Нет доступа")
    return JobStatusOut.model_validate(job)

@predict_async_route.get(
    "/jobs/user/{user_id}",
    response_model=List[JobOut],
    summary="Список задач пользователя"
)
def jobs_by_user(
    user_id: int,
    session: Session = Depends(get_session),
    _: TokenData = Depends(self_or_admin),
) -> List[JobOut]:
    rows = list_jobs_by_user(user_id, session)
    return rows
