from dataclasses import dataclass
from .user import User
from .logs import TaskLog, TransactionLog, TransactionHistory
from .theme import Theme
from .models import MLModel
from .wallet import Wallet

REWARD_BY_DIFFICULTY = {
    "easy": 2.0,
    "medium": 3.0,
    "hard": 4.0,
}

@dataclass
class TaskRequest:
    """
    Запрос на выполнение задания.
    Содержит пользователя, тему, модель и информацию о типе задания (базовое или бонусное).
    """
    user: User
    model: MLModel
    theme: Theme
    wallet: Wallet
    transactions: TransactionHistory
    is_bonus_comic: bool = False
    bonus_cost: float = 0.0

    def execute(self) -> TaskLog:
        if self.is_bonus_comic:
            if not self.wallet.deduct(self.bonus_cost):
                raise ValueError("Недостаточно баллов для бонусного задания")
            self.transactions.log(TransactionLog(self.user.id, -self.bonus_cost, 'debit', "bonus comic"))

        result = self.model.generate_task(self.theme, is_bonus=self.is_bonus_comic)
        log = TaskLog(
            user_id=self.user.id,
            task_description=f"{'Бонус' if self.is_bonus_comic else 'Базовое'} задание: {self.theme.name}",
            result=result,
            model_name=self.model.name,
            credits_spent=self.bonus_cost if self.is_bonus_comic else 0.0
        )
        self.user.log_task(log)
        print(f"\n✅ Пройдено {'бонусное' if self.is_bonus_comic else 'базовое'} задание: {result.explanation}")

        if result.is_correct and not self.is_bonus_comic:
            reward = REWARD_BY_DIFFICULTY.get(result.difficulty, 3.0)
            self.wallet.add(reward) #, reason="успешное выполнение задания")
            self.transactions.log(TransactionLog(self.user.id, reward, 'credit', "успешное выполнение задания"))
            print(f"💡 Начислено баллов: {reward} (сложность: {result.difficulty}), текущий баланс: {self.user.wallet.balance}")
        return log
