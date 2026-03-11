import importlib


def test_health_endpoint():
    app_module = importlib.import_module("app")
    client = app_module.app.test_client()
    res = client.get("/health")
    assert res.status_code == 200
    assert res.get_json()["status"] == "ok"


def test_start_then_answer_invalid_session():
    app_module = importlib.import_module("app")
    client = app_module.app.test_client()
    start = client.get("/start").get_json()
    assert "session_id" in start

    # invalid session should be rejected
    res = client.post(
        "/answer",
        json={
            "session_id": "not-a-real-session",
            "feature": "language",
            "value": "English",
            "answer": "yes",
        },
    )
    assert res.status_code == 400


def test_sessions_and_insights_endpoints_exist():
    app_module = importlib.import_module("app")
    client = app_module.app.test_client()
    assert client.get("/sessions").status_code == 200
    assert client.get("/insights").status_code == 200

