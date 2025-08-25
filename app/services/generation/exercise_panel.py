# app/services/generation/exercise_panel.py
from __future__ import annotations
import random
from typing import List
from pydantic import BaseModel

from services.llm.ollama_client import generate_exercises as ollama_generate

# На вход — "сырой" словарь упражнения, на выход — pydantic-модель в роутере
class RawExercise(BaseModel):
    prompt: str
    choices: List[str] = []
    answer: str

FALLBACK_BANK = {
    "A1": {
        "ser/estar": [
            ("Yo ___ estudiante.", ["soy", "estoy", "eres", "somos"], "soy"),
            ("Madrid ___ en España.", ["es", "está", "eres", "son"], "está"),
            ("Nosotros ___ amigos.", ["somos", "estamos", "sois", "están"], "somos"),
        ],
        "vocabulario básica": [
            ("Elige la traducción de 'casa':", ["house", "dog", "water", "car"], "house"),
            ("Elige la traducción de 'libro':", ["book", "tree", "door", "food"], "book"),
            ("¿Qué significa 'grande'?:", ["big", "small", "clean", "old"], "big"),
        ],
        "artículos": [
            ("___ gato es negro.", ["El", "La", "Los", "Las"], "El"),
            ("___ mesa es grande.", ["El", "La", "Los", "Un"], "La"),
            ("Quiero ___ manzana.", ["un", "una", "unos", "unas"], "una"),
        ],
    },
    # Можно расширять для A2/B1...
}

def _fallback_generate(theme_name: str, count: int, level: str) -> List[RawExercise]:
    bank = FALLBACK_BANK.get(level.upper()) or FALLBACK_BANK["A1"]
    # из банка берём любую тему, если нет точного совпадения
    pool: List[tuple[str, List[str], str]] = []
    for entries in bank.values():
        pool.extend(entries)

    random.shuffle(pool)
    picked = pool[:max(1, count - 1)]  # оставим место для бонуса, если понадобится в роутере

    result = [RawExercise(prompt=p, choices=c, answer=a) for (p, c, a) in picked]
    return result

def build_panel(theme_name: str, count: int, level: str) -> List[RawExercise]:
    """
    Пробуем Ollama; при неудаче — аккуратный fallback.
    """
    items = ollama_generate(theme_name=theme_name, count=count, level=level)
    if items:
        # преобразуем в RawExercise
        cleaned = []
        for it in items[:count]:
            try:
                cleaned.append(RawExercise(**it))
            except Exception:
                continue
        if cleaned:
            return cleaned
    # fallback
    return _fallback_generate(theme_name, count, level)
