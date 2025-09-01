import logging
import os
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.pool import StaticPool
from .config import get_settings

from models.transaction_log import TransactionLog
from models.task_log import TaskLog, TaskResult
from models.prediction_log import PredictionLog
from models.wallet import Wallet
from models.user import User
from models.theme import Theme
from models.exercise import Exercise


logger = logging.getLogger(__name__)
settings = get_settings()

def get_database_engine():
    # Тестовый режим → SQLite in-memory с StaticPool
    if getattr(settings, "TESTING", False) or os.getenv("TESTING") == "1":
        return create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    # предупредим, если используем дефолты
    defaults = settings.defaults_used()
    if defaults:
        logger.warning(
            "Settings: используются значения по умолчанию для: %s",
            ", ".join(defaults)
        )
    engine = create_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=3600
    )
    return engine

engine = get_database_engine()


def get_session():
    with Session(engine) as session:
        yield session
        
def init_db(drop_all: bool = False) -> None:
    try:
        if drop_all:
             SQLModel.metadata.drop_all(engine)
        SQLModel.metadata.create_all(engine)
    except Exception as e:
        print(f"[init_db] Ошибка при инициализации БД: {e}")
        raise

