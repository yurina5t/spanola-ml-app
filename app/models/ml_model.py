from abc import ABC, abstractmethod
from typing import List
from sqlmodel import Session
from models.user import User
from models.theme import Theme
from models.prediction_log import PredictionLog
from models.task_log import TaskResult


class MLModel(ABC):
    """
    Абстрактная модель генерации заданий.
    """
    def __init__(self, name: str, cost: float):
        self.name = name
        self.cost = cost

    @abstractmethod
    def generate_task(self, theme: Theme, is_bonus: bool = False) -> TaskResult:
        raise NotImplementedError

    def recommend_theme(self, user: User, themes: List[Theme], session: Session) -> Theme:
        used_explanations = {t.result.explanation for t in user.completed_tasks if t.result}
        for theme in themes:
            if theme.name not in used_explanations:
                self._log_prediction(user.id, theme, session)
                return theme
        fallback = themes[0]
        self._log_prediction(user.id, fallback, session)
        return fallback

    def _log_prediction(self, user_id: int, theme: Theme, session: Session):
        log = PredictionLog(
            user_id=user_id,
            model_name=self.name,
            theme_name=theme.name,
            difficulty=theme.level
        )
        session.add(log)
        session.commit()
