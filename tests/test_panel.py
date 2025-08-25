# tests/test_panel.py
from http import HTTPStatus

def _create_theme(client, admin_h, name="A1 - panel", level="A1"):
    r = client.post(
        "/api/themes/",
        headers=admin_h,
        json={"name": name, "level": level, "base_comic": "base.png", "bonus_comics": []},
    )
    assert r.status_code in (HTTPStatus.OK, HTTPStatus.CREATED), r.text
    return r.json()["id"]

def test_panel_free_no_charge(signup, as_admin, as_user, client):
    """POST /api/predictions/panel: бесплатная панель → без списаний, 15 упражнений."""
    user_id = signup("panel_free@example.com", "password123")
    admin_h = as_admin()
    user_h = as_user(user_id)
    theme_id = _create_theme(client, admin_h, name="A1 - ser/estar", level="A1")

    before = client.get(f"/api/wallet/{user_id}", headers=user_h).json()["balance"]

    r = client.post(
        "/api/predictions/panel",
        headers=user_h,
        json={"user_id": user_id, "theme_id": theme_id, "count": 15, "is_bonus": False},
    )
    assert r.status_code == HTTPStatus.OK, r.text
    body = r.json()
    assert body["count"] == 15
    assert body["bonus_included"] is False
    assert body["credits_spent"] == 0.0

    after = client.get(f"/api/wallet/{user_id}", headers=user_h).json()["balance"]
    assert after == before  # без списаний

def test_panel_bonus_insufficient(signup, as_admin, as_user, client):
    """POST /api/predictions/panel: бонус при нулевом балансе → 409."""
    user_id = signup("panel_insuf@example.com", "password123")
    admin_h = as_admin()
    user_h = as_user(user_id)
    theme_id = _create_theme(client, admin_h, name="A1 - nouns", level="A1")

    r = client.post(
        "/api/predictions/panel",
        headers=user_h,
        json={"user_id": user_id, "theme_id": theme_id, "count": 15, "is_bonus": True},
    )
    # роутер мапит "недостаточно" в 409
    assert r.status_code in (HTTPStatus.CONFLICT, HTTPStatus.BAD_REQUEST), r.text

def test_panel_bonus_after_topup(signup, as_admin, as_user, client):
    """POST /api/predictions/panel: после пополнения списывает 1 и добавляет бонус-задачу."""
    user_id = signup("panel_bonus@example.com", "password123")
    admin_h = as_admin()
    user_h = as_user(user_id)
    theme_id = _create_theme(client, admin_h, name="A1 - verbs", level="A1")

    # пополнили на 2
    _ = client.post(
        "/api/wallet/admin_top_up",
        headers=admin_h,
        json={"user_id": user_id, "amount": 2, "reason": "init"},
    )
    assert _.status_code == HTTPStatus.OK, _.text

    before = client.get(f"/api/wallet/{user_id}", headers=user_h).json()["balance"]

    r = client.post(
        "/api/predictions/panel",
        headers=user_h,
        json={"user_id": user_id, "theme_id": theme_id, "count": 15, "is_bonus": True},
    )
    assert r.status_code == HTTPStatus.OK, r.text
    body = r.json()
    # 15 базовых + 1 бонус = 16
    assert body["count"] == 16
    assert body["bonus_included"] is True
    assert body["credits_spent"] == 1.0

    after = client.get(f"/api/wallet/{user_id}", headers=user_h).json()["balance"]
    assert after == before - 1
    # сверим, что возвращаемый balance_after совпадает с фактическим
    assert float(body["balance_after"]) == float(after)

def test_panel_forbidden_other_user(signup, as_admin, as_user, client):
    """POST /api/predictions/panel: нельзя генерировать панель за другого пользователя → 403."""
    owner_id = signup("panel_owner@example.com", "password123")
    stranger_id = signup("panel_stranger@example.com", "password123")

    admin_h = as_admin()
    theme_id = _create_theme(client, admin_h, name="A1 - adjectives", level="A1")

    stranger_h = as_user(stranger_id)
    r = client.post(
        "/api/predictions/panel",
        headers=stranger_h,
        json={"user_id": owner_id, "theme_id": theme_id, "count": 15, "is_bonus": False},
    )
    assert r.status_code == HTTPStatus.FORBIDDEN, r.text
