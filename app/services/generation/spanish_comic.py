from __future__ import annotations
from typing import List

from models.ml_model import MLModel             
from models.theme import Theme
from models.task_log import TaskResult
from services.llm.ollama_client import (
    enabled as ollama_enabled,
    generate_comic_task,    
)

def _fallback_vocab_for(theme_name: str, level: str) -> list[str]:
        t = theme_name.lower()
        lvl = (level or "A1").upper()
        if "ser" in t:
            return ["ser","soy","eres","es"] if lvl=="A1" else ["ser","estar","es","está","somos"]
        if "adjetiv" in t or "прилагатель" in t:
            return ["grande","pequeño","bonito","feo"] if lvl=="A1" else ["más","menos","tan","como","mejor","peor"]
        if any(k in t for k in ["pasado","pretérito","perfecto","indefinido"]):
            return ["ayer","anoche","ya","todavía","nunca","siempre"]
        return ["palabra","nueva"]

class SpanishComicModel(MLModel):
    """
    Генератор задания-комикса.
    1) Пытаемся получить данные из Ollama.
    2) Если не получилось — возвращаем стабильный фолбэк (как раньше).
    """
    def __init__(self):
        super().__init__(name="SpanishComicModel", cost=0.0)

    def generate_task(self, theme: Theme, is_bonus: bool = False) -> TaskResult:
        # 1. выбираем файл комикса как раньше
        comic_file = theme.get_bonus_comic() if is_bonus else theme.base_comic
        if is_bonus and not comic_file:
            comic_file = theme.base_comic 
        if not comic_file:
            raise ValueError("Нет комикса для этой темы")

        # 2. Попытка через Ollama
        if ollama_enabled():
            data = generate_comic_task(theme_name=theme.name, level=theme.level, is_bonus=is_bonus)
            if data:
                vocab = data.get("vocabulary") or _fallback_vocab_for(theme.name, theme.level)
                explanation = f"{data.get('explanation', '')} (Комикс: {comic_file})".strip()
                return TaskResult(
                    difficulty=data.get("difficulty", "easy"),
                    vocabulary=vocab,
                    explanation=explanation,
                    is_correct=False,  # не начисляем на генерации
                )
        # 3.Фолбэк (как раньше)
        diff = "easy"
        vocab = _fallback_vocab_for(theme.name, theme.level)
        explanation = f"[{diff}]. Комикс: {comic_file} | Тема: {theme.name} | Уровень: {theme.level}"
        return TaskResult(difficulty=diff, vocabulary=vocab, explanation=explanation, is_correct=False)