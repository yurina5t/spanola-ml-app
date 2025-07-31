from dataclasses import dataclass

@dataclass
class Wallet:
    """
    Кошелёк пользователя — управляет только балансом.
    """
    user_id: int
    balance: float = 0.0

    def add(self, amount: float):
        self.balance += amount

    def deduct(self, amount: float) -> bool:
        if self.balance >= amount:
            self.balance -= amount
            return True
        return False
    