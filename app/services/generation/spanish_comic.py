from __future__ import annotations
from typing import List

from models.ml_model import MLModel             
from models.theme import Theme
from models.task_log import TaskResult
from services.llm.ollama_client import (
    enabled as ollama_enabled,
    generate_comic_task,    
)

class SpanishComicModel(MLModel):
    """
    Генератор задания-комикса.
    1) Пытаемся получить данные из Ollama.
    2) Если не получилось — возвращаем стабильный фолбэк (как раньше).
    """
    def __init__(self):
        super().__init__(name="SpanishComicModel", cost=0.0)

    def generate_task(self, theme: Theme, is_bonus: bool = False) -> TaskResult:
        # выбираем файл комикса как раньше
        comic_file = theme.get_bonus_comic() if is_bonus else theme.base_comic
        if not comic_file:
            raise ValueError(
                "Нет бонусных комиксов для этой темы" if is_bonus
                else "Нет базового комикса для этой темы"
            )

        # 1) Попытка через Ollama
        if ollama_enabled():
            data = generate_comic_task(theme_name=theme.name, level=theme.level, is_bonus=is_bonus)
            if data:
                explanation = f"{data['explanation']} (Комикс: {comic_file})"
                return TaskResult(
                    difficulty=data["difficulty"],
                    vocabulary=(data.get("vocabulary") or ["ser", "soy", "eres", "es"]),
                    explanation=explanation,
                )

        # 2) Фолбэк (как раньше)
        diff = "easy"
        vocab: List[str] = (
            ["ser", "soy", "eres", "es"]
            if theme.name.lower().strip() in {"глагол ser", "ser"} else ["palabra", "nueva"]
        )
        explanation = f"[{diff}]. Комикс: {comic_file} | Тема: {theme.name} | Уровень: {theme.level}"
        return TaskResult(difficulty=diff, vocabulary=vocab, explanation=explanation)