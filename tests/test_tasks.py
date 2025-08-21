from http import HTTPStatus


def test_task_submit_awards_points(
    signup,
    as_user,
    client,
):
    """POST /api/tasks/submit: за верное решение начисляет 1 балл и отражается в истории кошелька."""
    user_id = signup("solver@example.com", "password123")
    user_h = as_user(user_id)

    before = client.get(
        f"/api/wallet/{user_id}",
        headers=user_h,
    ).json()["balance"]

    r = client.post(
        "/api/tasks/submit",
        headers=user_h,
        json={
            "user_id": user_id,
            "model_name": "dummy",
            "task_description": "solve easy task",
            "difficulty": "easy",
            "vocabulary": ["ser", "soy"],
            "explanation": "…",
            "is_correct": True,
        },
    )
    assert r.status_code == HTTPStatus.OK, r.text
    assert r.json()["points_awarded"] == 1

    after = client.get(
        f"/api/wallet/{user_id}",
        headers=user_h,
    ).json()["balance"]
    assert after == before + 1

    hist = client.get(
        f"/api/wallet/history/{user_id}",
        headers=user_h,
    )
    assert hist.status_code == HTTPStatus.OK
    assert any(
        item.get("operation") == "credit"
        for item in hist.json()
        if isinstance(item, dict)
    )


def test_task_submit_validation_422(
    signup,
    as_user,
    client,
):
    """POST /api/tasks/submit: пропуск обязательных полей → 422."""
    user_id = signup("val@example.com", "password123")
    headers = as_user(user_id)

    r = client.post(
        "/api/tasks/submit",
        headers=headers,
        json={
            "user_id": user_id,
        },
    )
    assert r.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
