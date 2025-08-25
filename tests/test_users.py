from http import HTTPStatus


def test_signup_ok(signup, signin):
    """POST /api/users/signup + 
    /api/users/signin: базовый сценарий регистрации и входа."""
    uid = signup("u1@example.com", "password123")
    assert isinstance(uid, int)

    token = signin("u1@example.com", "password123")
    assert token


def test_signup_duplicate_conflict(client, signup):
    """POST /api/users/signup: повторная регистрация с тем же email → 409."""
    _ = signup("dup@example.com", "password123")

    r = client.post(
        "/api/users/signup",
        json={"email": "dup@example.com","password": "password123"},
    )
    assert r.status_code == HTTPStatus.CONFLICT, r.text


def test_signin_wrong_password(client, signup):
    """POST /api/users/signin: неверный пароль → 401/403/400."""
    _ = signup("wrongpass@example.com", "password123")

    r = client.post(
        "/api/users/signin",
        json={"email": "wrongpass@example.com","password": "bad"},
    )
    assert r.status_code in (
        HTTPStatus.UNAUTHORIZED,
        HTTPStatus.FORBIDDEN,
        HTTPStatus.BAD_REQUEST,
    ), r.text
