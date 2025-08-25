# tests/factories.py
from sqlmodel import Session, select
from models.user import User
from models.wallet import Wallet

def create_user(session: Session, email: str = "u@example.com", password: str = "x") -> User:
    u = User(email=email, password=password)
    session.add(u)
    session.commit()
    session.refresh(u)
    return u

def get_or_create_wallet(session: Session, user_id: int) -> Wallet:
    w = session.exec(select(Wallet).where(Wallet.user_id == user_id)).first()
    if not w:
        w = Wallet(user_id=user_id, balance=0)
        session.add(w)
        session.commit()
        session.refresh(w)
    return w
