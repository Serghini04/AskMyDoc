from app import main


def test_liveness(api_client):
    assert api_client.get("/health").json() == {"status": "healthy"}


def test_readiness_reports_each_dependency(api_client, monkeypatch):
    monkeypatch.setattr(main, "_check_database", lambda: "ok")
    monkeypatch.setattr(main, "_check_vector_store", lambda: "ok")
    ready = api_client.get("/health/ready")
    assert ready.status_code == 200
    assert ready.json() == {"status": "ready", "checks": {"database": "ok", "vector_store": "ok"}}

    monkeypatch.setattr(main, "_check_vector_store", lambda: "unreachable")
    degraded = api_client.get("/health/ready")
    assert degraded.status_code == 503
    assert degraded.json()["checks"]["vector_store"] == "unreachable"
