from abc import ABC, abstractmethod
from typing import List
from .theme import Theme
from .logs import TaskResult, PredictionLog, PredictionHistory
from .user import User


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

    def recommend_theme(self, user: User, themes: List[Theme], predictions: PredictionHistory) -> Theme:
        used = {log.result.explanation for log in user.completed_tasks}
        for theme in themes:
            if theme.name not in used:
                predictions.log(PredictionLog(
                    user_id=user.id,
                    model_name=self.name,
                    theme_name=theme.name,
                    difficulty=theme.level
                ))
                return theme
        fallback = themes[0]
        predictions.log(PredictionLog(
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