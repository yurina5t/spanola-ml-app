import re
from hashlib import sha256
from dataclasses import dataclass, field
from typing import List
from .logs import TaskLog
from .wallet import Wallet


@dataclass
class User:
    id: int
    email: str
    _password: str
    wallet: Wallet = field(init=False)
    completed_tasks: List[TaskLog] = field(default_factory=list)

    def __post_init__(self):
        self._validate_email()
        self._validate_password()
        self._password = sha256(self._password.encode()).hexdigest()
        self.wallet = Wallet(user_id=self.id)

    def _validate_email(self):
        pattern = re.compile(r'^[\w\.-]+@[\w\.-]+\.\w+$')
        if not pattern.match(self.email):
            raise ValueError("Неверный формат email")

    def _validate_password(self):
        if len(self._password) < 8:
            raise ValueError("Пароль должен содержать не менее 8 символов")

    def log_task(self, log: TaskLog):
        self.completed_tasks.append(log)
