"""Tests for obligation CRUD and status management endpoints."""

from datetime import date, timedelta


def _create_contract(client):
    resp = client.post("/api/v1/contracts", json={
        "title": "Test Contract",
        "counterparty": "Test Corp",
        "contract_type": "saas",
    })
    return resp.json()["id"]


def test_create_obligation(client):
    contract_id = _create_contract(client)
    resp = client.post("/api/v1/obligations", json={
        "contract_id": contract_id,
        "title": "Submit monthly report",
        "obligation_type": "reporting",
        "responsible_party": "us",
        "deadline_type": "recurring",
        "recurrence_pattern": "monthly",
        "risk_level": "medium",
        "deadline_date": str(date.today() + timedelta(days=30)),
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Submit monthly report"
    assert data["extraction_source"] == "manual"
    assert data["status"] == "pending"


def test_list_obligations(client):
    contract_id = _create_contract(client)
    client.post("/api/v1/obligations", json={
        "contract_id": contract_id,
        "title": "Obligation 1",
        "obligation_type": "payment",
        "responsible_party": "us",
        "deadline_type": "fixed",
    })
    client.post("/api/v1/obligations", json={
        "contract_id": contract_id,
        "title": "Obligation 2",
        "obligation_type": "compliance",
        "responsible_party": "counterparty",
        "deadline_type": "ongoing",
    })

    resp = client.get("/api/v1/obligations")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_filter_by_contract(client):
    c1 = _create_contract(client)
    c2_resp = client.post("/api/v1/contracts", json={
        "title": "Other Contract",
        "counterparty": "Other Corp",
        "contract_type": "vendor",
    })
    c2 = c2_resp.json()["id"]

    client.post("/api/v1/obligations", json={
        "contract_id": c1,
        "title": "C1 Obligation",
        "obligation_type": "payment",
        "responsible_party": "us",
        "deadline_type": "fixed",
    })
    client.post("/api/v1/obligations", json={
        "contract_id": c2,
        "title": "C2 Obligation",
        "obligation_type": "sla",
        "responsible_party": "counterparty",
        "deadline_type": "recurring",
    })

    resp = client.get(f"/api/v1/obligations?contract_id={c1}")
    assert len(resp.json()) == 1
    assert resp.json()[0]["title"] == "C1 Obligation"


def test_change_status(client):
    contract_id = _create_contract(client)
    create_resp = client.post("/api/v1/obligations", json={
        "contract_id": contract_id,
        "title": "Status Test",
        "obligation_type": "delivery",
        "responsible_party": "us",
        "deadline_type": "fixed",
    })
    ob_id = create_resp.json()["id"]

    # Change to in_progress
    resp = client.patch(f"/api/v1/obligations/{ob_id}/status", json={
        "new_status": "in_progress",
        "notes": "Started working on it",
    })
    assert resp.status_code == 200
    assert resp.json()["status"] == "in_progress"

    # Change to completed
    resp = client.patch(f"/api/v1/obligations/{ob_id}/status", json={
        "new_status": "completed",
    })
    assert resp.json()["status"] == "completed"
    assert resp.json()["completed_at"] is not None

    # Check history
    assert len(resp.json()["status_history"]) == 2


def test_change_status_waived(client):
    contract_id = _create_contract(client)
    create_resp = client.post("/api/v1/obligations", json={
        "contract_id": contract_id,
        "title": "Waive Test",
        "obligation_type": "notification",
        "responsible_party": "both",
        "deadline_type": "event_triggered",
    })
    ob_id = create_resp.json()["id"]

    resp = client.patch(f"/api/v1/obligations/{ob_id}/status", json={
        "new_status": "waived",
        "notes": "Counterparty agreed to waive",
    })
    assert resp.json()["status"] == "waived"


def test_delete_obligation(client):
    contract_id = _create_contract(client)
    create_resp = client.post("/api/v1/obligations", json={
        "contract_id": contract_id,
        "title": "To Delete",
        "obligation_type": "other",
        "responsible_party": "us",
        "deadline_type": "fixed",
    })
    ob_id = create_resp.json()["id"]

    resp = client.delete(f"/api/v1/obligations/{ob_id}")
    assert resp.status_code == 204

    resp = client.get(f"/api/v1/obligations/{ob_id}")
    assert resp.status_code == 404


def test_upcoming_obligations(client):
    contract_id = _create_contract(client)
    # Due in 5 days
    client.post("/api/v1/obligations", json={
        "contract_id": contract_id,
        "title": "Due Soon",
        "obligation_type": "payment",
        "responsible_party": "us",
        "deadline_type": "fixed",
        "deadline_date": str(date.today() + timedelta(days=5)),
    })
    # Due in 60 days (outside 30-day window)
    client.post("/api/v1/obligations", json={
        "contract_id": contract_id,
        "title": "Due Later",
        "obligation_type": "reporting",
        "responsible_party": "us",
        "deadline_type": "fixed",
        "deadline_date": str(date.today() + timedelta(days=60)),
    })

    resp = client.get("/api/v1/obligations/upcoming?days=30")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["title"] == "Due Soon"


def test_obligation_for_nonexistent_contract(client):
    resp = client.post("/api/v1/obligations", json={
        "contract_id": 9999,
        "title": "Orphan",
        "obligation_type": "payment",
        "responsible_party": "us",
        "deadline_type": "fixed",
    })
    assert resp.status_code == 404
