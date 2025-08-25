# tests/test_wallet.py
from http import HTTPStatus

def test_admin_top_up_and_balance(client, signup, as_admin, as_user):
    uid = signup("wal1@example.com", "password123")
    user_h = as_user(uid)
    admin_h = as_admin()

    r = client.post("/api/wallet/admin_top_up",
                    headers=admin_h,
                    json={"user_id": uid, "amount": 5, "reason": "init"})
    assert r.status_code == HTTPStatus.OK, r.text

    r = client.get(f"/api/wallet/{uid}", headers=user_h)
    assert r.status_code == HTTPStatus.OK, r.text
    assert r.json()["balance"] == 5


def test_spend_on_bonus_insufficient_then_ok(client, signup, as_admin, as_user):
    uid = signup("wal2@example.com", "password123")
    user_h = as_user(uid)
    admin_h = as_admin()

    # без денег: ожидаем ошибку (возможны 400/404/409/422 в зависимости от реализации)
    r0 = client.post("/api/wallet/spend_on_bonus",
                     headers=user_h,
                     json={"user_id": uid, "amount": 2})
    assert r0.status_code in (400, 404, 409, 422), r0.text

    # пополняем и тратим
    r = client.post("/api/wallet/admin_top_up",
                    headers=admin_h,
                    json={"user_id": uid, "amount": 3, "reason": "refill"})
    assert r.status_code == HTTPStatus.OK, r.text

    r = client.post("/api/wallet/spend_on_bonus",
                    headers=user_h,
                    json={"user_id": uid, "amount": 2})
    assert r.status_code == HTTPStatus.OK, r.text

    # баланс стал 1
    r = client.get(f"/api/wallet/{uid}", headers=user_h)
    assert r.status_code == HTTPStatus.OK
    assert r.json()["balance"] == 1


def test_spend_on_bonus_forbidden_on_other_user(client, signup, as_user):
    owner = signup("owner@example.com", "password123")
    stranger = signup("stranger@example.com", "password123")
    stranger_h = as_user(stranger)

    # пытаемся списать у владельца чужими руками → 403
    r = client.post("/api/wallet/spend_on_bonus",
                    headers=stranger_h,
                    json={"user_id": owner, "amount": 1})
    assert r.status_code == HTTPStatus.FORBIDDEN, r.text


def test_can_spend(client, signup, as_admin, as_user):
    uid = signup("wal3@example.com", "password123")
    user_h = as_user(uid)
    admin_h = as_admin()

    # пополнили на 2
    client.post("/api/wallet/admin_top_up",
                headers=admin_h,
                json={"user_id": uid, "amount": 2, "reason": "init"})

    r_false = client.get(f"/api/wallet/can_spend/{uid}/3", headers=user_h)
    assert r_false.status_code == HTTPStatus.OK
    assert r_false.json()["can_spend"] is False

    r_true = client.get(f"/api/wallet/can_spend/{uid}/2", headers=user_h)
    assert r_true.status_code == HTTPStatus.OK
    assert r_true.json()["can_spend"] is True


def test_history_has_entries(client, signup, as_admin, as_user):
    uid = signup("wal4@example.com", "password123")
    user_h = as_user(uid)
    admin_h = as_admin()

    client.post("/api/wallet/admin_top_up",
                headers=admin_h,
                json={"user_id": uid, "amount": 4, "reason": "init"})
    client.post("/api/wallet/spend_on_bonus",
                headers=user_h,
                json={"user_id": uid, "amount": 1})

    r = client.get(f"/api/wallet/history/{uid}", headers=user_h)
    assert r.status_code == HTTPStatus.OK, r.text
    data = r.json()
    assert isinstance(data, list) and len(data) >= 1
    # минимальная проверка структуры
    assert {"amount"} <= set(data[0].keys())
