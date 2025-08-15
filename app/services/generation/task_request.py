from sqlmodel import Session
from models.user import User
from models.theme import Theme
from models.task_log import TaskLog, TaskResult
from models.transaction_log import TransactionLog
from models.ml_model import MLModel
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.wallet import Wallet

REWARD_BY_DIFFICULTY = {
    "easy": 2.0,
    "medium": 3.0,
    "hard": 4.0,
}


class TaskRequest:
    def __init__(
        self,
        user: User,
        theme: Theme,
        model: MLModel,
        session: Session,
        is_bonus_comic: bool = False,
        bonus_cost: float = 0.0
    ):
        self.user = user
        self.theme = theme
        self.model = model
        self.session = session
        self.is_bonus_comic = is_bonus_comic
        self.bonus_cost = bonus_cost

    def execute(self) -> TaskLog:
        # 1. Списание баллов за бонус
        if self.is_bonus_comic:
            if self.user.wallet.balance < self.bonus_cost:
                raise ValueError("Недостаточно баллов для бонусного задания")

            self.user.wallet.balance -= self.bonus_cost
            self._log_transaction(-self.bonus_cost, "bonus comic")
            self.session.refresh(self.user.wallet)

        # 2. Генерация задания
        result = self.model.generate_task(self.theme, is_bonus=self.is_bonus_comic)

        # 3. Сохраняем TaskLog
        log = TaskLog(
            user_id=self.user.id,
            theme_id=self.theme.id,
            task_description=f"{'Бонус' if self.is_bonus_comic else 'Базовое'} задание: {self.theme.name}",
            model_name=self.model.name,
            credits_spent=self.bonus_cost if self.is_bonus_comic else 0.0,
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
            is_correct=result.is_correct,
        )
        self.session.add(task_result)

        # 5. Начисление баллов за успешное выполнение
        if result.is_correct and not self.is_bonus_comic:
            reward = REWARD_BY_DIFFICULTY.get(result.difficulty, 3.0)
            self.user.wallet.balance += reward
            self._log_transaction(reward, "Успешное выполнение задания")

        self.session.commit()
        log.result = task_result
        return log

    def _log_transaction(self, amount: float, reason: str):
        transaction = TransactionLog(
            user_id=self.user.id,
            amount=amount,
            operation="credit" if amount > 0 else "debit",
            reason=reason,
        )
        self.session.add(transaction)
