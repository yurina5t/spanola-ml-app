from http import HTTPStatus


def test_predict_deducts_balance(
    signup,
    as_admin,
    as_user,
    client,
):
    """POST /api/predictions/: списывает кредиты и уменьшает баланс."""
    user_id = signup("paying@example.com", "password123")

    admin_h = as_admin()
    _ = client.post(
        "/api/wallet/admin_top_up",
        headers=admin_h,
        json={
            "user_id": user_id,
            "amount": 10,
            "reason": "test refill",
        },
    )
    assert _.status_code == HTTPStatus.OK, _.text

    user_h = as_user(user_id)
    before = client.get(
        f"/api/wallet/{user_id}",
        headers=user_h,
    ).json()["balance"]

    theme_id = client.post(
        "/api/themes/",
        headers=admin_h,
        json={
            "name": "A1 - ser",
            "level": "A1",
            "base_comic": "base.png",
            "bonus_comics": [],
        },
    ).json()["id"]

    r = client.post(
        "/api/predictions/",
        headers=user_h,
        json={
            "user_id": user_id,
            "theme_id": theme_id,
            "is_bonus": False,
        },
    )
    assert r.status_code == HTTPStatus.OK, r.text
    spent = r.json().get("credits_spent", 1)

    after = client.get(
        f"/api/wallet/{user_id}",
        headers=user_h,
    ).json()["balance"]
    assert after == before - spent


def test_predict_forbidden_other_user(
    signup,
    as_admin,
    as_user,
    client,
):
    """POST /api/predictions/: запрет предсказывать за другого пользователя → 403."""
    owner_id = signup("owner@example.com", "password123")
    stranger_id = signup("stranger@example.com", "password123")

    admin_h = as_admin()
    theme_id = client.post(
        "/api/themes/",
        headers=admin_h,
        json={
            "name": "A1 - adjectives",
            "level": "A1",
            "base_comic": "base.png",
            "bonus_comics": [],
        },
    ).json()["id"]

    stranger_h = as_user(stranger_id)
    r = client.post(
        "/api/predictions/",
        headers=stranger_h,
        json={
            "user_id": owner_id,
            "theme_id": theme_id,
            "is_bonus": False,
        },
    )
    assert r.status_code == HTTPStatus.FORBIDDEN, r.text


def test_predict_insufficient_balance(
    signup,
    as_user,
    as_admin,
    client,
):
    """POST /api/predictions/: для bonus при нулевом балансе → 409/400."""
    user_id = signup("poor@example.com", "password123")
    admin_h = as_admin()

    theme_id = client.post(
        "/api/themes/",
        headers=admin_h,
        json={
            "name": "A1 - nouns",
            "level": "A1",
            "base_comic": "base.png",
            "bonus_comics": [],
        },
    ).json()["id"]

    user_h = as_user(user_id)
    r = client.post(
        "/api/predictions/",
        headers=user_h,
        json={
            "user_id": user_id,
            "theme_id": theme_id,
            "is_bonus": True,  # бонус платный → при 0 балансе ждём 409/400
        },
    )
    assert r.status_code in (
        HTTPStatus.CONFLICT,
        HTTPStatus.BAD_REQUEST,
    ), r.text


def test_predictions_history_has_entries(
    signup,
    as_admin,
    as_user,
    client,
):
    """GET /api/predictions/history/{user_id}: содержит записи после предсказания."""
    user_id = signup("hist@example.com", "password123")
    admin_h = as_admin()
    user_h = as_user(user_id)

    _ = client.post(
        "/api/wallet/admin_top_up",
        headers=admin_h,
        json={
            "user_id": user_id,
            "amount": 5,
            "reason": "init",
        },
    )
    assert _.status_code in (HTTPStatus.OK, HTTPStatus.CREATED), _.text

    theme_id = client.post(
        "/api/themes/",
        headers=admin_h,
        json={
            "name": "A1 - verbs",
            "level": "A1",
            "base_comic": "base.png",
            "bonus_comics": [],
        },
    ).json()["id"]

    _ = client.post(
        "/api/predictions/",
        headers=user_h,
        json={
            "user_id": user_id,
            "theme_id": theme_id,
            "is_bonus": False,
        },
    )
    assert _.status_code == HTTPStatus.OK, _.text

    r = client.get(
        f"/api/predictions/history/{user_id}",
        headers=user_h,
    )
    assert r.status_code == HTTPStatus.OK
    payload = r.json()
    assert isinstance(payload, list) and len(payload) >= 1

    keys = {
        "model_name",
        "theme_name",
        "difficulty",
        "recommended_at",
    }
    assert keys.issubset(set(payload[0].keys()))
