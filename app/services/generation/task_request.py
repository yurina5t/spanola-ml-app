from sqlmodel import Session
from models.user import User
from models.theme import Theme
from models.task_log import TaskLog, TaskResult
from models.ml_model import MLModel
from services.crud.wallet import (
    deduct_for_reason_no_commit,
    credit_for_reason_no_commit,
)


class TaskRequest:
    """
    Генерация задания:
    - списывает 1 балл ТОЛЬКО за бонусное упражнение (bonus_cost),
    - при сбое генерации возвращает списанное,
    - не начисляет награду (начисление делаем в /submit после проверки ответов).
    """
    def __init__(
        self,
        user: User,
        theme: Theme,
        model: MLModel,
        session: Session,
        is_bonus_comic: bool = False,
        bonus_cost: float = 1.0,  # по умолчанию 1 балл
    ):
        self.user = user
        self.theme = theme
        self.model = model
        self.session = session
        self.is_bonus_comic = is_bonus_comic
        self.bonus_cost = bonus_cost

    def execute(self) -> TaskLog:
        debited = 0.0
        # 1. Списание баллов за бонус
        if self.is_bonus_comic:
            cost = float(self.bonus_cost or 1.0)
            if cost > 0: 
                deduct_for_reason_no_commit(self.user.id, cost, "Списание за бонусный комикс", self.session)
            self.session.commit()
            debited = cost

        # 2. Генерация задания
        try:
            result = self.model.generate_task(self.theme, is_bonus=self.is_bonus_comic)
        except Exception:
            if debited > 0:
                credit_for_reason_no_commit(self.user.id, debited, "Возврат за неудачную генерацию", self.session)
                self.session.commit()
            raise

        # 3. Сохраняем TaskLog
        log = TaskLog(
            user_id=self.user.id,
            theme_id=self.theme.id,
            task_description=f"{'Бонус' if self.is_bonus_comic else 'Базовое'} задание: {self.theme.name}",
            model_name=self.model.name,
            credits_spent=debited,
        )
        self.session.add(log)
        self.session.commit()
        self.session.refresh(log)

        # 4. Сохраняем TaskResult
        task_result = TaskResult(
            task_log_id=log.id,
            difficulty=result.difficulty,
            vocabulary=result.vocabulary,
            explanation=result.explanation,
            is_correct=False,
        )
        self.session.add(task_result)
        self.session.commit()

        log.result = task_result
        return log