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
    Теперь вызывающая сторона отвечает за commit().
    """
    # 1. Создаём TaskLog
    log = TaskLog(
        user_id=user_id,
        task_description=task_description,
        model_name=model_name,
        credits_spent=credits_spent
    )
    session.add(log)

    # 2. Создаём TaskResult и привязываем к TaskLog
    result = TaskResult(
        #task_log_id=log.id, заполним после flush(), чтобы id уже был
        difficulty=difficulty,
        vocabulary=vocabulary,
        explanation=explanation,
        is_correct=is_correct
    )
    # сначала обеспечим появление log.id
    session.flush()
    result.task_log_id = log.id

    session.add(result)

    # 3. Привязываем к объекту и возвращаем
    log.result = result
    return log


def get_tasks_by_user(user_id: int, session: Session) -> List[TaskLog]:
    statement = select(TaskLog).where(TaskLog.user_id == user_id)
    return session.exec(statement).all()


def get_task_by_id(task_id: int, session: Session) -> Optional[TaskLog]:
    statement = select(TaskLog).where(TaskLog.id == task_id)
    return session.exec(statement).first()