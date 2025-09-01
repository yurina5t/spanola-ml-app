#app/schemas/panel.py
from typing import List, Optional
from pydantic import BaseModel

class PanelQuestion(BaseModel):
    id: str
    prompt: str
    choices: Optional[List[str]] = None

class PanelPayload(BaseModel):
    exercise_id: int
    theme_id: int
    level: str
    instructions: str
    difficulty: str
    questions: List[PanelQuestion]
