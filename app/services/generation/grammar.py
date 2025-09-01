# app/services/generation/grammar.py
import random
from models.ml_model import MLModel
from models.theme import Theme
from models.task_log import TaskResult


def grammar_focus(theme_name: str, level: str) -> str:
    t = (theme_name or "").lower()
    lvl = (level or "A1").upper()

    if "ser" in t:
        return "A1: спряжение 'ser' в настоящем времени." if lvl == "A1" \
            else "A2: контраст 'ser' vs 'estar' в типичных ситуациях."
    if "adjetiv" in t or "прилагатель" in t:
        return "A1: согласование прилагательных по роду/числу." if lvl == "A1" \
            else "A2: сравнительные конструкции (más/menos/tan ... como)."
    if any(k in t for k in ["pasado", "pretérito", "perfecto", "indefinido"]):
        return "A2: contraste pretérito perfecto vs indefinido (частые маркеры)."
    if lvl.startswith("B1"):
        return "B1: subjuntivo básico, se impersonal, perífrasis."
    if lvl.startswith("B2"):
        return "B2: condicional tipo 2, relativos avanzados, estilo indirecto."
    return f"{lvl}: задания соответствующие уровню, без редких исключений."

def _fallback_vocab_for(theme_name: str, level: str) -> list[str]:
    t = (theme_name or "").lower()
    lvl = (level or "A1").upper()
    if "ser" in t:
        return ["ser", "soy", "eres", "es"] if lvl == "A1" else ["ser", "estar", "es", "está", "somos"]
    if "adjetiv" in t or "прилагатель" in t:
        return ["grande", "pequeño", "bonito", "feo"] if lvl == "A1" else ["más", "menos", "tan", "como", "mejor", "peor"]
    if any(k in t for k in ["pasado", "pretérito", "perfecto", "indefinido"]):
        return ["ayer", "anoche", "ya", "todavía", "nunca", "siempre"]
    if lvl.startswith("B1"):
        return ["ojalá", "es importante que", "se dice", "llevar + gerundio"]
    if lvl.startswith("B2"):
        return ["si + imp. subj.", "condicional", "lo que", "cuyo", "había + participio"]
    return ["palabra", "nueva"]
# --- распределения сложностей по уровням ---
_DIFF_DIST = {
    "A1": {"easy": 0.7, "medium": 0.3, "hard": 0.0},
    "A2": {"easy": 0.2, "medium": 0.6, "hard": 0.2},
    "B1": {"easy": 0.1, "medium": 0.5, "hard": 0.4},
    "B2": {"easy": 0.05, "medium": 0.35, "hard": 0.60},
}
def _normalize_level(level: str) -> str:
    lvl = (level or "A1").strip().upper()
    for key in ("A1", "A2", "B1", "B2"):
        if lvl.startswith(key):
            return key
    return "A1"

def _sample_from_dist(dist: dict[str, float]) -> str:
    # нормализуем и выбираем
    items = list(dist.items())
    total = sum(w for _, w in items) or 1.0
    r = random.random() * total
    acc = 0.0
    for label, w in items:
        acc += w
        if r <= acc:
            return label
    return items[-1][0]

def _tweak_dist_for_theme(level: str, theme_name: str, is_bonus: bool) -> dict[str, float]:
    """Опционально корректируем распределение под тему/бонус."""
    base = _DIFF_DIST[_normalize_level(level)].copy()
    t = (theme_name or "").lower()

    # Бонусные задания чуть сложнее
    if is_bonus:
        base["hard"] += 0.1
        base["medium"] += 0.05
        base["easy"] = max(0.0, base["easy"] - 0.15)

    # Для «ser vs estar» на A2 можем чаще давать medium/hard
    if "ser" in t and _normalize_level(level) == "A2":
        base["hard"] += 0.1
        base["medium"] += 0.1
        base["easy"] = max(0.0, base["easy"] - 0.2)

    # Нормализуем
    s = sum(base.values()) or 1.0
    for k in base:
        base[k] = max(0.0, base[k] / s)
    return base

def _choose_difficulty(level: str, theme_name: str, is_bonus: bool) -> str:
    dist = _tweak_dist_for_theme(level, theme_name, is_bonus)
    return _sample_from_dist(dist)

class GrammarModel(MLModel):
    def __init__(self):
        super().__init__(name="GrammarModel", cost=0.0)

    def generate_task(self, theme: Theme, is_bonus: bool = False) -> TaskResult:
        difficulty = _choose_difficulty(theme.level, theme.name, is_bonus)
        focus = grammar_focus(theme.name, theme.level)
        vocab = _fallback_vocab_for(theme.name, theme.level)

        explanation = f"{focus} | Тема: {theme.name} | Уровень: {theme.level} | Сложность: {difficulty}"

        return TaskResult(
            difficulty=difficulty,
            vocabulary=vocab,
            explanation=explanation,
            is_correct=False
        )