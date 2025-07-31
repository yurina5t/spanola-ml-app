from dataclasses import dataclass, field
from datetime import datetime
from typing import List

@dataclass
class TransactionLog:
    """
    Лог операций с баллами пользователя.
    Хранит информацию о начислениях или списаниях.
    """
    user_id: int
    amount: float
    operation: str  # 'credit' или 'debit'
    reason: str
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class TransactionHistory:
    """
    Сервис хранения истории транзакций отдельно от кошелька.
    """
    _logs: List[TransactionLog] = field(default_factory=list)

    def log(self, entry: TransactionLog):
        self._logs.append(entry)

    def get_user_history(self, user_id: int) -> List[TransactionLog]:
        return [log for log in self._logs if log.user_id == user_id]


@dataclass
class PredictionLog:
    """
    Лог предсказаний модели для пользователя.
    """
    user_id: int
    model_name: str
    theme_name: str
    difficulty: str
    recommended_at: datetime = field(default_factory=datetime.now)

@dataclass
class PredictionHistory:
    """
    Сервис хранения истории предсказаний.
    """
    _logs: List[PredictionLog] = field(default_factory=list)

    def log(self, entry: PredictionLog):
        self._logs.append(entry)

    def get_user_history(self, user_id: int) -> List[PredictionLog]:
        return [log for log in self._logs if log.user_id == user_id]
    
@dataclass
class TaskResult:
    """
    Результат выполнения задания.
    Содержит уровень задания, список слов и объяснение к заданному комиксу.
    """
    difficulty: str # "easy", "medium", "hard"
    vocabulary: List[str]
    explanation: str
    is_correct: bool = True


@dataclass
class TaskLog:
    """
    Лог завершённого задания.
    Сохраняет описание задания, результат, модель и дату выполнения.
    """
    user_id: int
    task_description: str
    result: TaskResult
    model_name: str
    credits_spent: float
    timestamp: datetime = field(default_factory=datetime.now)