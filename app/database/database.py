from sqlmodel import SQLModel, Session, create_engine 
from contextlib import contextmanager
from .config import get_settings

from models.transaction_log import TransactionLog
from models.task_log import TaskLog, TaskResult
from models.prediction_log import PredictionLog
from models.wallet import Wallet
from models.user import User
from models.theme import Theme

def get_database_engine():
    settings = get_settings()
    engine = create_engine(
        url=settings.DATABASE_URL_psycopg,
        echo=settings.DEBUG,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=3600
    )
    return engine

engine = get_database_engine()

@contextmanager
def get_session():
    with Session(engine) as session:
        yield session
        
def init_db(drop_all: bool = False) -> None:
    try:
        if drop_all:
                for model in [
                     TaskResult, 
                     PredictionLog, 
                     TransactionLog, 
                     TaskLog, 
                     Wallet,  
                     User, 
                     Theme
                ]:
                    model.__table__.drop(engine, checkfirst=True)
        SQLModel.metadata.create_all(engine)
    except Exception as e:
        print(f"[init_db] Ошибка при инициализации БД: {e}")
        raise

