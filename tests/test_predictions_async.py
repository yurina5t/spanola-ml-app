from http import HTTPStatus


def test_async_job_charges_and_publishes(
    signup,
    as_admin,
    as_user,
    client,
    monkeypatch,
):
    """POST /api/predictions/async: списывает 1 кредит и публикует задачу в очередь."""
    user_id = signup("async@example.com", "password123")
    admin_h = as_admin()
    user_h = as_user(user_id)

    _ = client.post(
        "/api/wallet/admin_top_up",
        headers=admin_h,
        json={
            "user_id": user_id,
            "amount": 3,
            "reason": "init",
        },
    )
    assert _.status_code in (HTTPStatus.OK, HTTPStatus.CREATED), _.text

    theme_id = client.post(
        "/api/themes/",
        headers=admin_h,
        json={
            "name": "A1 - async",
            "level": "A1",
            "base_comic": "base.png",
            "bonus_comics": [],
        },
    ).json()["id"]

    before = client.get(
        f"/api/wallet/{user_id}",
        headers=user_h,
    ).json()["balance"]

    published = {}

    def fake_publish(queue_name: str, message: dict):
        published["queue"] = queue_name
        published["msg"] = message

    patched = False
    for dotted in (
        "routers.prediction_async.publish_task",
        "app.mq.publisher.publish_task",
        "app.services.mq.publisher.publish_task",
        "mq.publisher.publish_task",
    ):
        try:
            monkeypatch.setattr(dotted, fake_publish, raising=False)
            patched = True
        except Exception:
            continue

    assert patched, "Не удалось замокать publish_task — проверь путь к модулю MQ"

    r = client.post(
        "/api/predictions/async",
        headers=user_h,
        json={
            "user_id": user_id,
            "theme_id": theme_id,
            "model_type": "comic",
            "is_bonus": True, 
        },
    )
    assert r.status_code in (HTTPStatus.ACCEPTED, HTTPStatus.OK), r.text

    job = r.json()
    assert job.get("status") in {"pending", "processing", "queued"}
    assert published.get("queue")
    assert "job_id" in (published.get("msg") or {})

    after = client.get(
        f"/api/wallet/{user_id}",
        headers=user_h,
    ).json()["balance"]
    assert after == before - 1

    r = client.get(
        f"/api/predictions/jobs/{job['id']}",
        headers=user_h,
    )
    assert r.status_code == HTTPStatus.OK

    r = client.get(
        f"/api/predictions/jobs/user/{user_id}",
        headers=user_h,
    )
    assert r.status_code == HTTPStatus.OK
    assert any(
        j["id"] == job["id"]
        for j in r.json()
    )
