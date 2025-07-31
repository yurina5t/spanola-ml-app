from dataclasses import dataclass
from typing import List

from .user import User
from .logs import TaskLog, TransactionLog, TransactionHistory

@dataclass
class Admin(User):
    """
    Класс администратора платформы.
    Может пополнять баланс других пользователей и просматривать их историю заданий.
    """
    def top_up_user(self, user: User, amount: float, transactions: TransactionHistory):
        user.wallet.add(amount)
        transactions.log(TransactionLog(
            user_id=user.id, 
            amount=amount, 
            operation="credit",
            reason="Пополнение администратором"
            ))

    def view_all_logs(self, users: List[User]) -> List['TaskLog']:
        logs = []
        for u in users:
            logs.extend(u.completed_tasks)
        return logs
