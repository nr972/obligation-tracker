"""Tests for demo data loading and clearing."""


def test_load_sample_data(client):
    resp = client.post("/api/v1/demo/load")
    assert resp.status_code == 200
    data = resp.json()
    assert data["loaded"] > 0

    # Verify contracts were created
    contracts = client.get("/api/v1/contracts").json()
    assert len(contracts) == 8

    # Verify obligations were created
    obligations = client.get("/api/v1/obligations").json()
    assert len(obligations) > 30


def test_load_sample_data_idempotent(client):
    client.post("/api/v1/demo/load")
    first_count = len(client.get("/api/v1/contracts").json())

    # Loading again should not duplicate
    client.post("/api/v1/demo/load")
    second_count = len(client.get("/api/v1/contracts").json())
    assert first_count == second_count


def test_clear_sample_data(client):
    client.post("/api/v1/demo/load")
    assert len(client.get("/api/v1/contracts").json()) > 0

    resp = client.post("/api/v1/demo/reset")
    assert resp.status_code == 200
    assert resp.json()["cleared"] == 8

    assert len(client.get("/api/v1/contracts").json()) == 0


def test_sample_data_has_health_scores(client):
    client.post("/api/v1/demo/load")
    contracts = client.get("/api/v1/contracts").json()
    scored = [c for c in contracts if c["health_score"] is not None]
    assert len(scored) == len(contracts)


def test_sample_obligations_have_source(client):
    client.post("/api/v1/demo/load")
    obligations = client.get("/api/v1/obligations").json()
    for ob in obligations:
        assert ob["extraction_source"] == "sample"


def test_config_mode(client):
    resp = client.get("/api/v1/config/mode")
    assert resp.status_code == 200
    data = resp.json()
    assert "ai_enabled" in data
    assert "demo_mode" in data
