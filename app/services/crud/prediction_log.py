from sqlmodel import Session, select
from models.prediction_log import PredictionLog
from typing import List


def log_prediction(
    user_id: int,
    model_name: str,
    theme_name: str,
    difficulty: str,
    session: Session
) -> PredictionLog:
    """
    Сохранить лог рекомендации темы пользователю.
    """
    log = PredictionLog(
        user_id=user_id,
        model_name=model_name,
        theme_name=theme_name,
        difficulty=difficulty
    )
    session.add(log)
    session.commit()
    session.refresh(log)
    return log


def get_predictions_by_user(user_id: int, session: Session) -> List[PredictionLog]:
    """
    Получить историю рекомендаций для пользователя.
    """
    statement = select(PredictionLog).where(PredictionLog.user_id == user_id)
    return session.exec(statement).all()
