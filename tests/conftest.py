# tests/conftest.py
import os, sys, pytest
os.environ.setdefault("TESTING", "1")

from http import HTTPStatus
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import Session as SASession
from sqlalchemy import event

APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app"))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from api import app
from database.database import get_session
try:
    from dependencies.auth import authenticate, TokenData
except Exception:
    authenticate = None
    # fallback TokenData, если импорт не удался
    from dataclasses import dataclass
    @dataclass
    class TokenData:
        email: str | None = None
        user_id: int | None = None
        role: str = "user"

@pytest.fixture(scope="session")
def engine():
    eng = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # включаем FK-каскады в SQLite
    @event.listens_for(eng, "connect")
    def _fk_on(dbapi_connection, connection_record):  # noqa: ARG001
        cur = dbapi_connection.cursor()
        cur.execute("PRAGMA foreign_keys=ON;")
        cur.close()

    # импорт моделей до create_all
    import models.user            # type: ignore[reportUnusedImport]
    import models.wallet          # type: ignore[reportUnusedImport]
    try:
        import models.transaction_log  # type: ignore[reportUnusedImport]
        import models.task_log         # type: ignore[reportUnusedImport]
        import models.prediction_log   # type: ignore[reportUnusedImport]
    except Exception:
        pass

    SQLModel.metadata.create_all(eng)
    return eng


@pytest.fixture
def connection(engine):
    conn = engine.connect()
    tx = conn.begin()
    try:
        yield conn
    finally:
        tx.rollback()
        conn.close()


@pytest.fixture
def session(connection):
    s = SASession(bind=connection)
    s.begin_nested()  # создаём SAVEPOINT

    @event.listens_for(SASession, "after_transaction_end")
    def _restart_savepoint(sess, trans):
        # после commit() вложенной транзакции — заново открыть SAVEPOINT
        if trans.nested and not getattr(trans, "_parent", None):
            try:
                sess.begin_nested()
            except Exception:
                pass

    try:
        yield s
    finally:
        s.close()
        # аккуратно снять слушатель (чтобы не протекал между тестами)
        try:
            event.remove(SASession, "after_transaction_end", _restart_savepoint)
        except Exception:
            pass


@pytest.fixture
def client(session: Session):
    def _get_session_override():
        return session

    app.dependency_overrides[get_session] = _get_session_override
    # базовый аноним/юзер override; точечные — через as_user/as_admin ниже
    if authenticate is not None:
        app.dependency_overrides[authenticate] = lambda: TokenData(email="user@test.local", user_id=0, role="user")

    c = TestClient(app)
    try:
        yield c
    finally:
        app.dependency_overrides.clear()


# ---------- фикстуры авторизации ----------
@pytest.fixture
def as_user():
    """Подменяет authenticate так, чтобы текущий пользователь был с ролью 'user'."""
    def _use(user_id: int, email: str | None = None):
        if authenticate is not None:
            app.dependency_overrides[authenticate] = (
                lambda: TokenData(email=email or f"user{user_id}@test.local", user_id=user_id, role="user")
            )
        return {"Authorization": "Bearer test-user"}
    return _use


@pytest.fixture
def as_admin():
    """Подменяет authenticate так, чтобы текущий пользователь был админом."""
    def _use(email: str = "admin@test.local"):
        if authenticate is not None:
            app.dependency_overrides[authenticate] = (
                lambda: TokenData(email=email, user_id=0, role="admin")
            )
        return {"Authorization": "Bearer test-admin"}
    return _use



@pytest.fixture
def signup(client: TestClient):
    def _do(email: str, password: str) -> int:
        r = client.post("/api/users/signup", json={"email": email, "password": password})
        assert r.status_code in (HTTPStatus.CREATED, HTTPStatus.OK), r.text
        body = r.json()
        return int(body.get("user_id") or body.get("id"))
    return _do

@pytest.fixture
def signin(client: TestClient):
    def _do(email: str, password: str) -> str:
        r = client.post("/api/users/signin", json={"email": email, "password": password})
        assert r.status_code == HTTPStatus.OK, r.text
        return r.json().get("access_token") or r.json().get("token")
    return _do

# быстрый админ-топап
@pytest.fixture
def topup(client):
    def _topup(headers, user_id: int, amount: int, reason: str = "init"):
        return client.post(
            "/api/wallet/admin_top_up",
            headers=headers,
            json={"user_id": user_id, "amount": amount, "reason": reason},
        )
    return _topup

# создание темы
@pytest.fixture
def create_theme(client):
    def _create(headers, name: str = "A1 - test", level: str = "A1"):
        r = client.post(
            "/api/themes/",
            headers=headers,
            json={"name": name, "level": level, "base_comic": "base.png", "bonus_comics": []},
        )
        r.raise_for_status()
        return r.json()["id"]
    return _create

# получить баланс
@pytest.fixture
def balance(client):
    def _balance(headers, user_id: int) -> float:
        r = client.get(f"/api/wallet/{user_id}", headers=headers)
        assert r.status_code == HTTPStatus.OK, r.text
        return r.json()["balance"]
    return _balance