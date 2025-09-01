# app/services/llm/ollama_client.py
from __future__ import annotations
import os, json, logging, requests, random
from typing import Any, List, Dict, Optional

logger = logging.getLogger(__name__)

USE_OLLAMA = os.getenv("USE_OLLAMA", "0").lower() in {"1", "true", "yes"}
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b-instruct")
REQUEST_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "20"))  # seconds
TEMPERATURE = float(os.getenv("OLLAMA_TEMPERATURE", "0.3"))
MAX_TOKENS = int(os.getenv("OLLAMA_MAX_TOKENS", "800"))
TOKENS_COMIC = int(os.getenv("OLLAMA_TOKENS_COMIC", "200"))
TOKENS_PANEL = int(os.getenv("OLLAMA_TOKENS_PANEL", str(MAX_TOKENS)))
TOKENS_PER_ITEM = int(os.getenv("OLLAMA_TOKENS_PER_ITEM", "150"))

# Профили уровней (можешь дополнять)
LEVEL_GUIDE = {
    "A1": {
        "lexicon": "vocabulario muy básico del día a día",
        "grammar": "presente de indicativo; ser/estar; artículos; adjetivos básicos; preposiciones simples",
        "length": "frases cortas (<= 10-12 palabras)",
        "avoid": "tiempos pasados/condicional/subjuntivo; oraciones complejas",
    },
    "A2": {
        "lexicon": "vocabulario cotidiano más amplio",
        "grammar": "presente; pretérito indefinido; perífrasis básicas (ir a + inf.); comparativos",
        "length": "frases cortas-medias (<= 14 palabras)",
        "avoid": "subjuntivo; oraciones muy complejas",
    },
    "B1": {
        "lexicon": "temas frecuentes y algo abstractos",
        "grammar": "presente; pasados (indef./impf.); futuro; condicional simple; subjuntivo presente en estructuras frecuentes",
        "length": "frases medias (<= 18 palabras)",
        "avoid": "construcciones raras o poco frecuentes",
    },
    "B2": {
        "lexicon": "temas variados, incluido abstracto",
        "grammar": "todos los tiempos principales; subjuntivo frecuente; pasivas sencillas",
        "length": "frases medias-largas (<= 22 palabras)",
        "avoid": "tecnicismos innecesarios",
    },
}

TASK_TYPES = [
    "completar hueco con la forma correcta",
    "elegir sinónimos o antónimos básicos",
    "elegir la palabra que complete mejor la frase",
    "elegir la forma correcta de ser/estar/tiempo verbal permitido",
]

def enabled() -> bool:
    return USE_OLLAMA

def _strip_code_fences(text: str) -> str:
    t = (text or "").strip()
    if t.startswith("```"):
        t = t.strip("` \n")
        if t[:4].lower() == "json":
            t = t[4:].lstrip()
    return t

def _build_prompt(theme_name: str, count: int, level: str, theme_desc: Optional[str]) -> str:
    guide = LEVEL_GUIDE.get(level.upper(), LEVEL_GUIDE["A1"])
    # 2-3 типа заданий на партию — для разнообразия
    picked = random.sample(TASK_TYPES, k=min(3, len(TASK_TYPES)))
    extra = f"Descripción del tema: {theme_desc}." if theme_desc else ""
    return f"""
Eres profesor de ELE (Español como Lengua Extranjera).
Genera EXACTAMENTE {count} ejercicios tipo test en español para nivel {level}.
Tema: "{theme_name}". {extra}

Respeta el perfil del nivel:
- Léxico: {guide['lexicon']}
- Gramática: {guide['grammar']}
- Longitud de frase: {guide['length']}
- Evitar: {guide['avoid']}

Varía los tipos de ejercicio entre: {", ".join(picked)}.
Cada ejercicio es un objeto JSON con claves:
- "prompt": enunciado breve y claro en español;
- "choices": array de 4 opciones plausibles (strings);
- "answer": string con la ÚNICA opción correcta (debe estar en "choices").

REQUISITOS:
- Usa SOLO estructuras propias del nivel {level}.
- Longitud del enunciado acorde al nivel.
- No repitas enunciados ni respuestas.
- Salida: SOLO un array JSON con {count} objetos (sin comentarios, sin markdown).
""".strip()

def _clean_and_validate(items: List[Dict[str, Any]], count: int) -> List[Dict[str, Any]]:
    cleaned: List[Dict[str, Any]] = []
    seen_prompts = set()

    for it in items:
        if not isinstance(it, dict): 
            continue
        prompt = str(it.get("prompt") or "").strip()
        raw_choices = it.get("choices") or []
        choices = [str(c).strip() for c in raw_choices if str(c).strip()]
        answer  = str(it.get("answer") or "").strip()

        if not prompt or not choices:
            continue

        # дедупликация вариантов с сохранением порядка
        choices = list(dict.fromkeys(choices))

        # если правильного ответа нет в вариантах — вставим его
        if answer and answer not in choices:
            if len(choices) < 4:
                choices.append(answer)
            else:
                choices[-1] = answer

        # ограничим/допаддим до ровно 4
        if len(choices) > 4:
            choices = choices[:4]
            if answer and answer not in choices:
                choices[-1] = answer
        while len(choices) < 4:
            choices.append("—")
        # перетасуем, чтобы правильный не залипал на одной позиции
        random.shuffle(choices)

        # Убираем дубли
        key = (prompt.lower(), tuple(c.lower() for c in choices))
        if key in seen_prompts:
            continue
        seen_prompts.add(key)

        answer_final = answer or next((c for c in choices if c != "—"), choices[0])
        cleaned.append({"prompt": prompt, "choices": choices, "answer": answer_final})

        if len(cleaned) >= max(1, int(count)):
            break
    return cleaned

def _coerce_to_list(parsed):
    if isinstance(parsed, list):
        return parsed
    if isinstance(parsed, dict):
        for key in ("items", "questions", "exercises", "data", "result"):
            v = parsed.get(key)
            if isinstance(v, list):
                return v
        vals = list(parsed.values())
        if vals and all(isinstance(x, dict) for x in vals):
            return vals
        return [parsed]
    return []


def generate_exercises(
        theme_name: str, 
        count: int, 
        level: str, 
        theme_desc: Optional[str] = None,
    ) -> Optional[List[Dict[str, Any]]]:
    """
    Запрашивает у Ollama массив JSON-объектов упражнений.
    Возвращает уже «прибранный» список через _clean_and_validate(...) или None (для fallback).
    """
    if not enabled():
        logger.info("Ollama disabled via USE_OLLAMA; skipping call.")
        return None

    url = f"{OLLAMA_HOST}/api/generate"
    prompt = _build_prompt(theme_name, count, level, theme_desc)
    num_predict = max(TOKENS_PANEL, TOKENS_PER_ITEM * max(1, int(count)))

    try:
        resp = requests.post(
            url,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "options": {"temperature": TEMPERATURE, "num_predict": num_predict},
                "stream": False,
                "format": "json",
            },
            timeout=REQUEST_TIMEOUT,
        )
        if resp.status_code != 200:
            logger.warning("Ollama non-200: %s %s", resp.status_code, resp.text[:800])
            return None

        data = resp.json()
        text = (data or {}).get("response", "").strip()
        text = _strip_code_fences(text)
        if not text:
            logger.warning("Ollama returned empty response for panel.")
            return None
        
        # Пробуем распарсить как есть; если не вышло — вырезаем первый '[' и последний ']'
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            parsed = None
            # 1) попробуем вырезать первый массив [...]
            a1, a2 = text.find("["), text.rfind("]")
            if a1 != -1 and a2 != -1 and a2 > a1:
                try:
                    parsed = json.loads(text[a1:a2 + 1])
                except json.JSONDecodeError:
                    parsed = None
        # 2) если массива нет — попробуем объект {...}
            if parsed is None:
                o1, o2 = text.find("{"), text.rfind("}")
                if o1 != -1 and o2 != -1 and o2 > o1:
                    try:
                        parsed = json.loads(text[o1:o2 + 1])
                    except json.JSONDecodeError:
                        parsed = None
            if parsed is None:
                logger.warning("Ollama panel JSON decode failed (no list/object could be parsed).")
                return None
        # нормализуем к списку объектов
        parsed = _coerce_to_list(parsed)
        if not parsed:
            logger.warning("Ollama returned JSON but not an array/object list; fallback.")
            return None

        items = _clean_and_validate(parsed, count)
        return items or None

    except requests.RequestException as e:
        logger.error("Ollama request error: %s", e)
        return None
    except json.JSONDecodeError as e:
        logger.error("Ollama JSON parse error: %s", e)
        return None
    except Exception as e:
        logger.exception("Unexpected Ollama error: %s", e)
        return None

def _build_comic_prompt(theme_name: str, level: str, is_bonus: bool) -> str:
    bonus = " (BONUS)" if is_bonus else ""
    return f"""
Eres un asistente de enseñanza de español. Nivel: {level}. Tema: "{theme_name}"{bonus}.

Genera UN SOLO ejercicio breve relacionado con el tema.
Devuelve SOLO JSON (objeto) sin texto extra, sin markdown, sin comentarios, con el siguiente esquema:

{{
  "difficulty": "easy|medium|hard",
  "explanation": "Instrucción en ruso, 1-2 frases, ясная задача для ученика",
  "vocabulary": ["palabra1","palabra2","..."]  // 3-8 испанских слов по теме
}}

No incluyas nada más aparte del JSON.
""".strip()

def _post_ollama(payload, timeout):
    return requests.post(f"{OLLAMA_HOST}/api/generate", json=payload, timeout=timeout)

def generate_comic_task(theme_name: str, level: str, is_bonus: bool) -> Optional[Dict[str, Any]]:
    """Запрашивает у Ollama JSON: {difficulty, explanation, vocabulary[]} с 1–2 попытками."""
    if not enabled():
        logger.info("Ollama disabled via USE_OLLAMA; skipping comic generation.")
        return None

    prompt = _build_comic_prompt(theme_name, level, is_bonus)

    # две попытки: 1) обычная; 2) короче по токенам и холоднее по температуре
    attempts = [
        {"num_predict": TOKENS_COMIC,                   "temperature": TEMPERATURE, "timeout": REQUEST_TIMEOUT},
        #{"num_predict": max(120, TOKENS_COMIC // 2),   "temperature": 0.1,         "timeout": REQUEST_TIMEOUT * 2},
    ]

    last_err = None
    for i, opts in enumerate(attempts, start=1):
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "options": {"temperature": opts["temperature"], "num_predict": opts["num_predict"]},
            "stream": False,
            "format": "json",
        }
        try:
            resp = _post_ollama(payload, opts["timeout"])
            if resp.status_code != 200:
                logger.warning("Ollama non-200(comic) attempt %s: %s %s", i, resp.status_code, resp.text[:2000])
                last_err = f"HTTP {resp.status_code}"
                continue

            text = (resp.json() or {}).get("response", "").strip()
            text = _strip_code_fences(text)
            if not text:
                logger.warning("Ollama returned empty response for comic task (attempt %s).", i)
                last_err = "empty_response"
                continue

            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                start = text.find("{")
                end = text.rfind("}")
                if start != -1 and end != -1 and end > start:
                    data = json.loads(text[start:end+1])
                else:
                    raise

            diff = str(data.get("difficulty", "easy")).lower()
            if diff not in {"easy", "medium", "hard"}:
                diff = "easy"

            vocab = data.get("vocabulary") or []
            if not isinstance(vocab, list):
                vocab = []
            vocab = [str(x) for x in vocab][:10]

            expl = data.get("explanation")
            if not isinstance(expl, str) or not expl.strip():
                expl = f"[{diff}] Тема: {theme_name} | Уровень: {level}"

            return {"difficulty": diff, "explanation": expl.strip(), "vocabulary": vocab}

        except (requests.ReadTimeout, requests.ConnectTimeout) as e:
            logger.warning("Ollama timeout on comic attempt %s: %s", i, e)
            last_err = "timeout"
            continue
        except requests.RequestException as e:
            logger.error("Ollama request error (comic) attempt %s: %s", i, e)
            last_err = "request_error"
            continue
        except json.JSONDecodeError as e:
            logger.error("Ollama JSON parse error (comic) attempt %s: %s", i, e)
            last_err = "json_error"
            continue
        except Exception as e:
            logger.exception("Unexpected Ollama error (comic) attempt %s: %s", i, e)
            last_err = "unexpected"
            continue

    logger.warning("Comic generation failed after retries, reason: %s", last_err)
    return None
    
