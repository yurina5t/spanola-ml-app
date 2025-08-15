from typing import Optional, List, Any
from sqlmodel import Session, select
from datetime import datetime, timezone
from models.job import Job, JobStatus, ModelType

def create_job(*, user_id: int, theme_id: int, model_type: ModelType, session: Session) -> Job:
    job = Job(user_id=user_id, theme_id=theme_id, model_type=model_type)
    session.add(job)
    session.commit()
    session.refresh(job)
    return job

def get_job(job_id: int, session: Session) -> Optional[Job]:
    return session.get(Job, job_id)

def list_jobs_by_user(user_id: int, session: Session) -> List[Job]:
    st = select(Job).where(Job.user_id == user_id).order_by(Job.created_at.desc())
    return session.exec(st).all()

def set_status(job: Job, status: JobStatus, session: Session, *, result: Any = None, error: Optional[str] = None):
    job.status = status
    job.updated_at = datetime.now(timezone.utc)
    if result is not None:
        job.result = result
    if error is not None:
        job.error = error
    session.add(job)
    session.commit()
    session.refresh(job)
    return job
