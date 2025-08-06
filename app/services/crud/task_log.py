from sqlmodel import Session, select
from models.task_log import TaskLog, TaskResult
from typing import List, Optional


def log_task(
    user_id: int,
    task_description: str,
    model_name: str,
    credits_spent: float,
    difficulty: str,
    vocabulary: List[str],
    explanation: str,
    is_correct: bool,
    session: Session
) -> TaskLog:
    """
    Сохранить лог выполнения задания + результат.
    """
    # 1. Создаём TaskLog
    log = TaskLog(
        user_id=user_id,
        task_description=task_description,
        model_name=model_name,
        credits_spent=credits_spent
    )
    session.add(log)
    session.commit()  # чтобы log.id стал доступен
    session.refresh(log)

    # 2. Создаём TaskResult и привязываем к TaskLog
    result = TaskResult(
        task_log_id=log.id,
        difficulty=difficulty,
        vocabulary=vocabulary,
        explanation=explanation,
        is_correct=is_correct
    )
    session.add(result)
    session.commit()
    session.refresh(result)

    # 3. Привязываем к объекту и возвращаем
    log.result = result
    return log


def get_tasks_by_user(user_id: int, session: Session) -> List[TaskLog]:
    statement = select(TaskLog).where(TaskLog.user_id == user_id)
    return session.exec(statement).all()


def get_task_by_id(task_id: int, session: Session) -> Optional[TaskLog]:
    statement = select(TaskLog).where(TaskLog.id == task_id)
    return session.exec(statement).first()