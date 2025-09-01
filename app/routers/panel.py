# app/routers/panel.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
from sqlmodel import Session
import json, unicodedata

from database.database import engine
from models.exercise import Exercise
from models.theme import Theme
from schemas.panel import PanelPayload, PanelQuestion
from services.generation.exercise_panel import build_panel
from dependencies.auth import get_current_user
from services.crud.wallet import credit_for_reason_no_commit

router = APIRouter(prefix="/panel", tags=["panel"])

class SubmitBody(BaseModel):
    answers: Dict[str, str]

def _norm(s: str) -> str:
    s = (s or "").strip().lower()
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")

def _reward_points(difficulty: str, score: int) -> int:
    if score < 50:
        return 0
    base = {"easy": 1, "medium": 2, "hard": 3}
    pts = round(base.get(difficulty, 2) * (score / 100))
    return max(1, pts)


@router.post("/generate", response_model=PanelPayload)
def generate_panel(
    theme_id: int,
    count: int = 5,
    level: str = "A1",
    difficulty: Optional[str] = None, 
    user=Depends(get_current_user),
):
    """
    Генерируем вопросы, сохраняем полный набор (с ответами) в БД,
    клиенту отдаём без ответов.
    """
    with Session(engine) as s:
        theme = s.get(Theme, theme_id)
        if not theme:
            raise HTTPException(404, "Тема не найдена")

        raw = build_panel(theme.name, count, level)

        diff = (difficulty or "medium").lower()
        if diff not in {"easy", "medium", "hard"}:
            diff = "medium"

        payload_full = {
            "theme_id": theme_id,
            "level": level,
            "difficulty": diff,
            "questions": [q.model_dump() for q in raw],
        }

        ex = Exercise(
            user_id=user.user_id,
            theme_id=theme_id,
            level=level,
            difficulty=diff,
            payload_json=json.dumps(payload_full, ensure_ascii=False),
        )
        s.add(ex)
        s.commit()
        s.refresh(ex)

        client_payload = PanelPayload(
            exercise_id=ex.id,
            theme_id=theme_id,
            level=level,
            difficulty=diff,
            instructions=f"Отметь правильные ответы по теме: {theme.name}",
            questions=[PanelQuestion(id=q.id, prompt=q.prompt, choices=q.choices or None) for q in raw],
        )
        return client_payload


@router.post("/{exercise_id}/submit")
def submit_panel(exercise_id: int, body: SubmitBody, user=Depends(get_current_user)):
    with Session(engine) as session:
        ex = session.get(Exercise, exercise_id)
        if not ex or ex.user_id != user.user_id:
            raise HTTPException(404, "Упражнение не найдено.")

        payload = json.loads(ex.payload_json or "{}")
        gold_map = {q["id"]: (q.get("answer") or "") for q in payload.get("questions", [])}

        total = len(gold_map)
        correct = 0
        for qid, gold in gold_map.items():
            user_ans = body.answers.get(qid, "")
            if _norm(user_ans) == _norm(gold):
                correct += 1
        score = int(correct * 100 / total) if total else 0
        difficulty = (payload.get("difficulty") or "medium").lower()
        reward = _reward_points(difficulty, score)
        
        if reward:
            credit_for_reason_no_commit(user.user_id, reward, "Начисление за упражнение", session)

        session.commit()

    return {"score": score, "correct": correct, "total": total, "reward": reward}