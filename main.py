import re
from datetime import datetime
from typing import List, Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass, field



@dataclass
class User:
    """
    Класс пользователя платформы.
    
    Пользователь может проходить задания, получать баллы, тратить их
    на дополнительные комиксы и просматривать свою историю выполненных заданий.
    """
    id: int
    email: str
    password: str
    balance: float = 0.0
    completed_tasks: List['TaskLog'] = field(default_factory=list)

    def __post_init__(self):
        self._validate_email()
        self._validate_password()

    def _validate_email(self):
        pattern = re.compile(r'^[\w\.-]+@[\w\.-]+\.\w+$')
        if not pattern.match(self.email):
            raise ValueError("Неверный формат email")

    def _validate_password(self):
        if len(self.password) < 8:
            raise ValueError("Пароль должен содержать не менее 8 символов")

    def add_credits(self, amount: float) -> None:
        self.balance += amount

    def deduct_credits(self, amount: float) -> bool:
        if self.balance >= amount:
            self.balance -= amount
            return True
        return False

    def log_task(self, log: 'TaskLog'):
        self.completed_tasks.append(log)


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
    difficulty: str
    vocabulary: List[str]
    explanation: str


@dataclass
class TaskLog:
    """
    Лог завершённого задания.

    Хранит информацию о пользователе, теме, результате и затраченных баллах.
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

    От неё наследуются конкретные модели, реализующие метод generate_task,
    принимающий объект Theme и флаг бонусного задания.
    """
    def __init__(self, name: str, cost: float):
        self.name = name
        self.cost = cost
    
    @abstractmethod
    def generate_task(self, theme: 'Theme', is_bonus: bool = False) -> 'TaskResult':
        raise NotImplementedError("Метод generate_task должен быть реализован в подклассе")


class SpanishComicModel(MLModel):
    """
    Конкретная реализация ML-модели.

    Генерирует задания на основе заданной темы и уровня.
    """
    def __init__(self):
        super().__init__(name="SpanishComicModel", cost=0.0) 

    def generate_task(self, theme: Theme, is_bonus: bool = False) -> TaskResult:
        comic_file = theme.base_comic if not is_bonus else theme.get_bonus_comic()
        if not comic_file:
            raise ValueError("Нет доступных бонусных комиксов для этой темы")

        explanation = f"Комикс: {comic_file} | Тема: {theme.name} | Уровень: {theme.level}"
        vocab = ["ser", "soy", "eres", "es"] if theme.name == "глагол ser" else ["palabra", "nueva"]
        return TaskResult(difficulty=theme.level, vocabulary=vocab, explanation=explanation)



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
            if not self.user.deduct_credits(self.bonus_cost):
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
        return log


class Admin(User):
    """
    Класс администратора.

    Может пополнять баланс других пользователей и просматривать все логи.
    """
    def __init__(self, id: int, email: str, password: str):
        super().__init__(id, email, password)

    def top_up_user(self, user: User, amount: float):
        user.add_credits(amount)

    def view_all_logs(self, users: List[User]) -> List[TaskLog]:
        logs = []
        for u in users:
            logs.extend(u.completed_tasks)
        return logs


def main():
    try:
        # 1.Регистрация пользователя
        user = User(id=1, email="nuevo@correo.es", password="superclave123")
        print(f"✅ Зарегистрирован: {user.email}, баланс: {user.balance} баллов")

        # 2.Задаём тему
        ser_theme = Theme(
            name="глагол ser",
            level="A1",
            base_comic="comic_ser_base.jpg",
            bonus_comics=["comic_ser_bonus1.jpg"]
        )

        # 3.Модель
        model = SpanishComicModel()

        # 4.Выполнение базового задания
        base_task = TaskRequest(user=user, model=model, theme=ser_theme, is_bonus_comic=False)
        base_log = base_task.execute()
        print(f"\n✅ Пройдено базовое задание: {base_log.result.explanation}")

        # 5.Начисляем баллы
        reward_points = 3.0
        user.add_credits(reward_points)
        print(f"🎁 Начислено баллов: {reward_points}, текущий баланс: {user.balance}")

        # 6.Предлагаем бонусный комикс
        bonus_cost = 2.0
        print("\n💡 Доступен бонусный комикс на эту тему!")
        bonus_task = TaskRequest(user=user, model=model, theme=ser_theme, is_bonus_comic=True, bonus_cost=bonus_cost)
        bonus_log = bonus_task.execute()
        print(f"\n🔮 Пройден бонусный комикс: {bonus_log.result.explanation}")
        print(f"💎 Остаток баланса: {user.balance} баллов")

    except ValueError as e:
        print(f"❌ Ошибка: {e}")



if __name__ == "__main__":
    main()
