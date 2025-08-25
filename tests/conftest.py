# tests/conftest.py
import os, sys, pytest

APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app"))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

os.environ.setdefault("TESTING", "1")

from http import HTTPStatus
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session as SQLMSession
from sqlalchemy.orm import Session as SASession
from sqlalchemy import event

from api import app
from database.database import get_session
from dependencies.auth import get_current_user, get_current_admin
from dependencies.authz import self_or_admin
from schemas.auth import TokenData

@pytest.fixture(scope="session")
def engine():
    eng = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(eng, "connect")
    def _fk_on(dbapi_connection, connection_record):  # noqa: ARG001
        cur = dbapi_connection.cursor()
        cur.execute("PRAGMA foreign_keys=ON;")
        cur.close()

    # Важно: импортируем модели ДО create_all (и без префикса app.)
    import models.user          # noqa: F401
    import models.wallet        # noqa: F401
    try:
        import models.transaction_log  # noqa: F401
        import models.task_log         # noqa: F401
        import models.prediction_log   # noqa: F401
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
    s = SQLMSession(bind=connection)
    s.begin_nested()

    @event.listens_for(SASession, "after_transaction_end")
    def _restart_savepoint(sess, trans):
        parent = getattr(trans, "_parent", None)
        if trans.nested and parent is not None and not getattr(parent, "nested", False):
            sess.begin_nested()

    try:
        yield s
    finally:
        s.close()
        try:
            event.remove(SASession, "after_transaction_end", _restart_savepoint)
        except Exception:
            pass


@pytest.fixture
def client(session: SQLMSession):
    def _get_session_override():
        return session

    # подменяем сессию БД
    app.dependency_overrides[get_session] = _get_session_override

    # дефолт: гость = обычный юзер id=0 (если где-то потребуют)
    app.dependency_overrides[get_current_user] = lambda: TokenData(user_id=0, is_admin=False, email="guest@example.com")
    app.dependency_overrides[self_or_admin]   = lambda: TokenData(user_id=0, is_admin=True,  email="admin@example.com") 
    c = TestClient(app)
    try:
        yield c
    finally:
        app.dependency_overrides.clear()


# ---------- фикстуры авторизации ----------
@pytest.fixture
def as_user():
    """Делает текущего «юзера» с указанным user_id."""
    def _use(user_id: int, email: str | None = None):
        td = TokenData(user_id=user_id, is_admin=False, email=email or f"user{user_id}@example.com")
        app.dependency_overrides[get_current_user] = lambda td=td: td
        app.dependency_overrides[self_or_admin]    = lambda td=td: td
        return {"Authorization": "Bearer test-user"}
    return _use


@pytest.fixture
def as_admin():
    """Делает текущего «админа»."""
    def _use(email: str = "admin@example.com"):
        td = TokenData(user_id=0, is_admin=True, email=email)
        app.dependency_overrides[get_current_user] = lambda td=td: td
        app.dependency_overrides[get_current_admin] = lambda td=td: td
        app.dependency_overrides[self_or_admin]    = lambda td=td: td
        return {"Authorization": "Bearer test-admin"}
    return _use


# -------- хелперы API (если нужны в тестах) --------
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
