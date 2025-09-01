# app/services/generation/exercise_panel.py
from __future__ import annotations
import os
import logging
import random
from typing import List
from pydantic import BaseModel, Field
from services.llm.ollama_client import generate_exercises as ollama_generate
import concurrent.futures

SOFT_TIMEOUT = float(os.getenv("PANEL_SOFT_TIMEOUT", "20"))
DEFAULT_PANEL_COUNT = int(os.getenv("PANEL_DEFAULT_COUNT", "1"))
# На вход — "сырой" словарь упражнения, на выход — pydantic-модель в роутере
class RawExercise(BaseModel):
    id: str 
    prompt: str
    choices: List[str] = Field(default_factory=list)
    answer: str

FALLBACK_BANK = {
    "A1": {
        "ser/estar": [
            ("Yo ___ estudiante.", ["soy", "estoy", "eres", "somos"], "soy"),
            ("Madrid ___ en España.", ["es", "está", "eres", "son"], "está"),
            ("Nosotros ___ amigos.", ["somos", "estamos", "sois", "están"], "somos"),
        ],
        "adjetivos|прилагательные": [
            ("La casa es ____ (big).", ["grande", "pequeña", "buenos"], "grande"),
            ("El coche es ____ (old).", ["viejo", "vieja", "viejos"], "viejo"),
            ("Las flores son ____ (beautiful).", ["bonitas", "bonito", "bonita"], "bonitas"),
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
    "A2": {
        # прошедшее время: pretérito perfecto VS indefinido (без тонких исключений)
        "pretérito|pasado|perfecto|indefinido": [
            ("Esta mañana yo ____ (comer) tostadas.", ["he comido", "comí", "comía"], "he comido"),
            ("En 2010 nosotros ____ (viajar) a México.", ["hemos viajado", "viajamos", "viajábamos"], "viajamos"),
            ("¿______ (ver, tú) la película ya?", ["Has visto", "Viste", "Veías"], "Has visto"),
        ],
        # местоимения дополнения (le/lo/la/se/les/los/las) — базовые
        "pronombres de objeto|местоимения": [
            ("¿El libro? Yo ___ tengo.", ["lo", "le", "la"], "lo"),
            ("A María ___ escribo una carta.", ["la", "le", "lo"], "le"),
            ("Las llaves, no ___ encuentro.", ["las", "les", "los"], "las"),
        ],
        # сравнение прилагательных
        "comparativos|прилагательные": [
            ("Ana es ___ alta ___ Marta.", ["más ... que", "tan ... como", "menos ... que"], "más ... que"),
            ("Este coche es ___ rápido ___ el tuyo.", ["tan ... como", "más ... que", "menos ... que"], "tan ... como"),
            ("La casa es ___ cara ___ el piso.", ["menos ... que", "más ... que", "tan ... como"], "menos ... que"),
        ],
        # por/para
        "por|para": [
            ("Este regalo es ___ ti.", ["para", "por"], "para"),
            ("Caminamos ___ el parque.", ["por", "para"], "por"),
            ("Estudio español ___ trabajar en España.", ["para", "por"], "para"),
        ],
    },
    "B1": {
        # Presente de subjuntivo (триггеры: quiero que, es importante que, ojalá...)
        "subjuntivo|subjuntivo presente": [
            ("Ojalá que él ____ (venir) mañana.", ["venga", "viene", "vino"], "venga"),
            ("Es importante que nosotros ____ (estudiar).", ["estudiemos", "estudiamos", "estudiábamos"], "estudiemos"),
            ("Quiero que tú ____ (ser) puntual.", ["seas", "eres", "fuiste"], "seas"),
        ],
        # Se impersonal / pasiva refleja
        "se impersonal|pasiva refleja": [
            ("En esta tienda ____ (vender) libros.", ["se venden", "se vende", "venden"], "se venden"),
            ("____ (decir) que lloverá.", ["Se dice", "Se dicen", "Dicen se"], "Se dice"),
            ("Aquí no ____ (fumar).", ["se fuma", "se fuman", "fuma se"], "se fuma"),
        ],
        # Condicional simple
        "condicional": [
            ("Yo en tu lugar ____ (viajar) más.", ["viajaría", "viajaré", "viajaba"], "viajaría"),
            ("¿Qué ____ (hacer, tú) con un millón de euros?", ["harías", "hiciste", "haces"], "harías"),
            ("Ellos ____ (querer) venir, pero no pueden.", ["querrían", "quieren", "quisieron"], "querrían"),
        ],
        # Perífrasis verbales
        "perífrasis|perifrasis": [
            ("Acabo de ____ (llegar).", ["llegar", "llegado", "llegué"], "llegar"),
            ("Llevo dos años ____ (vivir) aquí.", ["viviendo", "vivido", "vivir"], "viviendo"),
            ("Voy a ____ (estudiar) esta noche.", ["estudiar", "estudiando", "estudié"], "estudiar"),
        ],
    },

    "B2": {
        # Oraciones condicionales tipo 2 (imperfecto de subjuntivo + condicional)
        "condicional tipo 2|si + imp. subj.": [
            ("Si yo ____ (tener) tiempo, ____ (viajar) más.", ["tuviera / viajaría", "tengo / viajaré", "tuve / viajé"], "tuviera / viajaría"),
            ("Si tú ____ (ser) más paciente, todo ____ (ir) mejor.", ["fueras / iría", "eres / irá", "fuiste / fue"], "fueras / iría"),
            ("Si ellos ____ (poder), te ____ (ayudar).", ["pudieran / ayudarían", "pueden / ayudarán", "pudieron / ayudaron"], "pudieran / ayudarían"),
        ],
        # Relativos avanzados (lo que, el cual, cuyo)
        "pronombres relativos|relativos": [
            ("No entiendo ____ dices.", ["lo que", "que lo", "el que"], "lo que"),
            ("La autora, ____ libros leíste, es famosa.", ["cuyos", "cuyo", "cuyas"], "cuyos"),
            ("La empresa para ____ trabajo es internacional.", ["la cual", "que la", "cuyo"], "la cual"),
        ],
        # Pluscuamperfecto / estilo indirecto básico
        "pluscuamperfecto|estilo indirecto": [
            ("Cuando llegué, ellos ya ____ (salir).", ["habían salido", "salieron", "han salido"], "habían salido"),
            ("Él dijo que ____ (estar) cansado.", ["estaba", "estuvo", "ha estado"], "estaba"),
            ("Pensé que ya lo ____ (hacer).", ["habías hecho", "hiciste", "has hecho"], "habías hecho"),
        ],
    },
}

def _normalize_level(level: str) -> str:
    lvl = (level or "A1").strip().upper()
    for key in ("A1", "A2", "B1", "B2"):
        if lvl.startswith(key):
            return key
    return "A1"

def _fallback_generate(theme_name: str, count: int, level: str) -> List[RawExercise]:
    bank = FALLBACK_BANK[_normalize_level(level)]
    # подбираем подходящую тему по ключам; если не нашли — берём всё подряд
    def _match_topic_key(theme_name: str, keys: list[str]) -> str | None:
        t = (theme_name or "").lower()
        for k in keys:
            for v in [s.strip() for s in k.split("|")]:
                if v and v in t:
                    return k
        return None
    
    topic_key = _match_topic_key(theme_name, list(bank.keys()))
    pool: list[tuple[str, list[str], str]] = []
    if topic_key:
        pool.extend(bank[topic_key])
    else:
        for lst in bank.values():
            pool.extend(lst)

    random.shuffle(pool)
    picked = pool[:max(1, count)]
    return [RawExercise(id=f"q{i}", prompt=p, choices=c, answer=a)
            for i, (p, c, a) in enumerate(picked, start=1)]

def build_panel(theme_name: str, count: int, level: str) -> List[RawExercise]:
    """
    Пробуем Ollama; при любой ошибке — мгновенный fallback.
    Можно принудительно форсировать заглушки через env PANEL_FORCE_FALLBACK=1.
    """
    # фиксируем 1 задание (или сколько укажешь в env)
    count = DEFAULT_PANEL_COUNT
    # Форсируем заглушки (удобно на деве/когда Ollama недоступен)
    if os.getenv("PANEL_FORCE_FALLBACK", "0") == "1":
        return _fallback_generate(theme_name, count, level)

    items = None
    try:
        # даём Ollama шанс, но не дольше SOFT_TIMEOUT секунд
        #items = ollama_generate(theme_name=theme_name, count=count, level=level)
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            fut = ex.submit(ollama_generate, theme_name=theme_name, count=count, level=level)
            items = fut.result(timeout=SOFT_TIMEOUT)
    except concurrent.futures.TimeoutError:
        logging.getLogger(__name__).warning("panel soft-timeout (%ss) -> fallback", SOFT_TIMEOUT)
        items = None
    except Exception as e:
        logging.getLogger(__name__).warning("Ollama failed, using fallback: %s", e)
        items = None

    if items:
        cleaned: List[RawExercise] = []
        for i, it in enumerate(items[:count], start=1):
            try:
                cleaned.append(RawExercise(
                    id=f"q{i}",
                    prompt=str(it.get("prompt") or "").strip(),
                    choices=[str(x) for x in (it.get("choices") or [])],
                    answer=str(it.get("answer") or "").strip(),
                ))
            except Exception:
                continue
        if cleaned:
            return cleaned

    # fallback всегда даёт результат
    return _fallback_generate(theme_name, count, level)