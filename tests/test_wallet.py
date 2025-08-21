# tests/test_wallet.py
from http import HTTPStatus

def test_spend_zero_then_ok(signup, as_user, as_admin, client):
    """POST /api/wallet/spend: при нуле — ошибка; 
    после пополнения — успешно списывает 2."""
    uid = signup("spendep@example.com", "password123")
    user_h = as_user(uid)

    r0 = client.post(
        "/api/wallet/spend", 
        headers=user_h, 
        json={"user_id": uid, "amount": 1}
    )
    assert r0.status_code in (
        HTTPStatus.BAD_REQUEST, 
        HTTPStatus.CONFLICT, 
        HTTPStatus.UNPROCESSABLE_ENTITY
    ), r0.text

    admin_h = as_admin()
    r1 = client.post(
        "/api/wallet/admin_top_up", 
        headers=admin_h, 
        json={"user_id": uid, "amount": 3, "reason": "init"}
    )
    assert r1.status_code in (
        HTTPStatus.OK, 
        HTTPStatus.CREATED
    ), r1.text

    before = client.get(f"/api/wallet/{uid}", headers=user_h).json()["balance"]
    r2 = client.post(
        "/api/wallet/spend", 
        headers=user_h, 
        json={"user_id": uid, "amount": 2}
    )
    assert r2.status_code in (
        HTTPStatus.OK, 
        HTTPStatus.CREATED
    ), r2.text

    after = client.get(f"/api/wallet/{uid}", headers=user_h).json()["balance"]
    assert after == before - 2


def test_can_spend_flag(signup, as_user, as_admin, client):
    """GET /api/wallet/can_spend: False для суммы > баланс; 
    True после пополнения."""
    uid = signup("canspend@example.com", "password123")
    user_h = as_user(uid)

    bal0 = client.get(f"/api/wallet/{uid}", headers=user_h).json()["balance"]
    r = client.get(
        "/api/wallet/can_spend", 
        headers=user_h, 
        params={"user_id": uid, "amount": bal0 + 1}
    )
    js = r.json()
    assert r.status_code == HTTPStatus.OK and (js is False or js.get("can") is False)

    admin_h = as_admin()
    client.post(
        "/api/wallet/admin_top_up", 
        headers=admin_h, 
        json={"user_id": uid, "amount": 5, "reason": "init"}
    )
    r = client.get(
        "/api/wallet/can_spend", 
        headers=user_h, 
        params={"user_id": uid, "amount": 3}
    )
    js = r.json()
    assert r.status_code == HTTPStatus.OK and (js is True or js.get("can") is True)


def test_deposit_increases_balance(signup, as_admin, as_user, client):
    """POST /api/wallet/deposit: 
    позитивный сценарий — баланс растёт ровно на сумму."""
    uid = signup("posdep@example.com", "password123")
    user_h = as_user(uid)
    admin_h = as_admin()

    before = client.get(f"/api/wallet/{uid}", headers=user_h).json()["balance"]
    r = client.post("/api/wallet/deposit", headers=admin_h, json={"user_id": uid, "amount": 7})
    assert r.status_code in (HTTPStatus.OK, HTTPStatus.CREATED), r.text
    after = client.get(f"/api/wallet/{uid}", headers=user_h).json()["balance"]
    assert after == before + 7


def test_deposit_negative_fails(signup, as_admin, client):
    """POST /api/wallet/deposit: отрицательная сумма → 400/409/422."""
    uid = signup("negdep@example.com", "password123")
    headers = as_admin()
    r = client.post(
        "/api/wallet/deposit", 
        headers=headers, 
        json={"user_id": uid, "amount": -5}
    )
    assert r.status_code in (
        HTTPStatus.BAD_REQUEST, 
        HTTPStatus.CONFLICT, 
        HTTPStatus.UNPROCESSABLE_ENTITY
    ), r.text


def test_history_has_entries(signup, as_user, as_admin, client):
    """GET /api/wallet/history/{user_id}: 
    возвращает непустой список после credit/debit."""
    uid = signup("history@example.com", "password123")
    user_h = as_user(uid)
    admin_h = as_admin()

    client.post(
        "/api/wallet/admin_top_up", 
        headers=admin_h, 
        json={"user_id": uid, "amount": 4, "reason": "init"}
    )
    client.post(
        "/api/wallet/spend", 
        headers=user_h, 
        json={"user_id": uid, "amount": 1}
    )

    r = client.get(f"/api/wallet/history/{uid}", headers=user_h)
    assert r.status_code == HTTPStatus.OK
    data = r.json()
    assert isinstance(data, list) and len(data) >= 1

    ops = {item.get("operation") for item in data if isinstance(item, dict)}
    assert "credit" in ops and "debit" in ops
