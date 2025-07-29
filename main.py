import re
from datetime import datetime
from typing import List, Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from hashlib import sha256

REWARD_BY_DIFFICULTY = {
    "easy": 2.0,
    "medium": 3.0,
    "hard": 4.0,
}

@dataclass
class TransactionLog:
    """
    Лог операций с баллами пользователя (начисление или списание баллов).

    Содержит сумму, тип операции и причину.
    """
    user_id: int
    amount: float
    operation: str  # 'credit' или 'debit'
    reason: str
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class PredictionLog:
    """
    Лог предсказаний модели для пользователя.

    Хранит информацию о модели, теме и времени рекомендации.
    """
    user_id: int
    model_name: str
    theme_name: str
    difficulty: str
    recommended_at: datetime = field(default_factory=datetime.now)

@dataclass
class Wallet:
    """
    Кошелёк пользователя.

    Отвечает за текущий баланс и ведёт историю транзакций.
    """
    user_id: int
    balance: float = 0.0
    transactions: List[TransactionLog] = field(default_factory=list)

    def add(self, amount: float, reason: str):
        self.balance += amount
        self.transactions.append(TransactionLog(self.user_id, amount, 'credit', reason))

    def deduct(self, amount: float, reason: str) -> bool:
        if self.balance >= amount:
            self.balance -= amount
            self.transactions.append(TransactionLog(self.user_id, -amount, 'debit', reason))
            return True
        return False


@dataclass
class User:
    """
    Класс пользователя платформы.

    Хранит email, хэш пароля, связанные задания и историю рекомендаций.
    Инициализирует кошелёк пользователя.
    """
    id: int
    email: str
    _password: str
    wallet: Wallet = field(init=False)
    completed_tasks: List['TaskLog'] = field(default_factory=list)
    prediction_history: List[PredictionLog] = field(default_factory=list)

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

    def log_task(self, log: 'TaskLog'):
        self.completed_tasks.append(log)

    def log_prediction(self, log: PredictionLog):
        self.prediction_history.append(log)    


@dataclass
class Theme:
    """
    Тематический модуль.

    Включает название темы, уровень сложности (A1, A2 и т.д.), базовый и бонусные комиксы.
    Используется при генерации заданий.
    """
    name: str
    level: str
    base_comic: str
    bonus_comics: List[str] = field(default_factory=list)

    def get_bonus_comic(self) -> Optional[str]:
        """Возвращает первый доступный бонусный комикс или None."""
        return self.bonus_comics[0] if self.bonus_comics else None


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


class MLModel(ABC):
    """
    Абстрактная модель генерации заданий.

    Предоставляет интерфейс для генерации заданий и рекомендаций тем.
    """
    def __init__(self, name: str, cost: float):
        self.name = name
        self.cost = cost
    
    @abstractmethod
    def generate_task(self, theme: 'Theme', is_bonus: bool = False) -> 'TaskResult':
        raise NotImplementedError("Метод generate_task должен быть реализован в подклассе")

    def recommend_theme(self, user: User, themes: List[Theme]) -> Theme:
        used = {log.result.explanation for log in user.completed_tasks}
        for theme in themes:
            if theme.name not in used:
                user.log_prediction(PredictionLog(
                    user_id=user.id,
                    model_name=self.name,
                    theme_name=theme.name,
                    difficulty=theme.level
                ))
                return theme
        fallback = themes[0]
        user.log_prediction(PredictionLog(
            user_id=user.id,
            model_name=self.name,
            theme_name=fallback.name,
            difficulty=fallback.level
        ))
        return fallback


class SpanishComicModel(MLModel):
    """
    Модель генерации заданий в формате комиксов.
    """
    def __init__(self):
        super().__init__(name="SpanishComicModel", cost=0.0) 

    def generate_task(self, theme: Theme, is_bonus: bool = False) -> TaskResult:
        comic_file = theme.base_comic if not is_bonus else theme.get_bonus_comic()
        if not comic_file:
            raise ValueError("Нет доступных бонусных комиксов для этой темы")

        explanation = f"[easy]. Комикс: {comic_file} | Тема: {theme.name} | Уровень: {theme.level}"
        vocab = ["ser", "soy", "eres", "es"] if theme.name == "глагол ser" else ["palabra", "nueva"]
        return TaskResult(difficulty="easy", vocabulary=vocab, explanation=explanation)

class GrammarModel(MLModel):
    def __init__(self):
        super().__init__(name="GrammarModel", cost=1.0)

    def generate_task(self, theme: Theme, is_bonus: bool = False) -> TaskResult:
        explanation = f"medium. Грамматическое упражнение по теме: {theme.name} | Уровень: {theme.level}"
        vocab = ["el verbo", "la conjugación", "el tiempo"]
        return TaskResult(difficulty="medium", vocabulary=vocab, explanation=explanation)

class VocabularyModel(MLModel):
    def __init__(self):
        super().__init__(name="VocabularyModel", cost=1.0)

    def generate_task(self, theme: Theme, is_bonus: bool = False) -> TaskResult:
        explanation = f"Упражнение на лексику по теме: {theme.name} | Уровень: {theme.level}"
        vocab = ["casa", "comida", "ropa"]
        return TaskResult(difficulty="medium", vocabulary=vocab, explanation=explanation)


@dataclass
class TaskRequest:
    """
    Запрос на выполнение задания.

    Содержит пользователя, тему, модель и информацию о типе задания (базовое или бонусное).
    """
    user: User
    model: MLModel
    theme: Theme
    is_bonus_comic: bool = False
    bonus_cost: float = 0.0

    def execute(self) -> TaskLog:
        if self.is_bonus_comic:
            if not self.user.wallet.deduct(self.bonus_cost, reason="bonus comic"):
                raise ValueError("Недостаточно баллов для бонусного задания")

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
            self.user.wallet.add(reward, reason="успешное выполнение задания")
            print(f"💡 Начислено баллов: {reward} (сложность: {result.difficulty}), текущий баланс: {self.user.wallet.balance}")
        return log


class Admin(User):
    """
    Класс администратора.

    Может пополнять баланс других пользователей и просматривать историю заданий пользователей.
    """
    def __init__(self, id: int, email: str, password: str):
        super().__init__(id, email, password)

    def top_up_user(self, user: User, amount: float):
        user.wallet.add(amount, reason="admin top-up" )

    def view_all_logs(self, users: List[User]) -> List[TaskLog]:
        logs = []
        for u in users:
            logs.extend(u.completed_tasks)
        return logs


def main():
    try:
        user = User(id=1, email="nuevo@correo.es", _password="superclave123")
        print(f"✅ Зарегистрирован: {user.email}, баланс: {user.wallet.balance} баллов")

        themes = [
            Theme(name="глагол ser", level="A1", base_comic="comic_ser_base.jpg", bonus_comics=["comic_ser_bonus1.jpg"]),
            Theme(name="прилагательные", level="A1", base_comic="comic_adj_base.jpg")
        ]

        model = GrammarModel()
        recommended = model.recommend_theme(user, themes)

        base_task = TaskRequest(user=user, model=model, theme=recommended, is_bonus_comic=False)
        base_log = base_task.execute()

        bonus_cost = 2.0
        print(f"\n🎁 Доступен бонусный комикс на эту тему! Стоимость: {bonus_cost} балла")
        bonus_task = TaskRequest(user=user, model=model, theme=recommended, is_bonus_comic=True, bonus_cost=bonus_cost)
        bonus_log = bonus_task.execute()
        
        print(f"💎 Остаток баланса: {user.wallet.balance} баллов")

        print("\n🧠 История рекомендаций:")
        for rec in user.prediction_history:
            print(f"  → {rec.model_name} рекомендовал: {rec.theme_name} ({rec.difficulty}) в {rec.recommended_at}")

    except ValueError as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    main()
