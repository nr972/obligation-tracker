"""Tests for health score computation."""

from datetime import date, timedelta


def _create_contract(client):
    resp = client.post("/api/v1/contracts", json={
        "title": "Score Test Contract",
        "counterparty": "Score Corp",
        "contract_type": "saas",
    })
    return resp.json()["id"]


def _add_obligation(client, contract_id, title, status="pending", risk_level="medium", days_from_now=None):
    data = {
        "contract_id": contract_id,
        "title": title,
        "obligation_type": "compliance",
        "responsible_party": "us",
        "deadline_type": "fixed",
        "risk_level": risk_level,
    }
    if days_from_now is not None:
        data["deadline_date"] = str(date.today() + timedelta(days=days_from_now))

    resp = client.post("/api/v1/obligations", json=data)
    ob_id = resp.json()["id"]

    if status != "pending":
        client.patch(f"/api/v1/obligations/{ob_id}/status", json={"new_status": status})

    return ob_id


def test_empty_contract_score(client):
    contract_id = _create_contract(client)
    resp = client.get(f"/api/v1/contracts/{contract_id}/health")
    assert resp.status_code == 200
    assert resp.json()["score"] == 100.0


def test_all_completed_score(client):
    contract_id = _create_contract(client)
    _add_obligation(client, contract_id, "Done 1", status="completed")
    _add_obligation(client, contract_id, "Done 2", status="completed")

    resp = client.get(f"/api/v1/contracts/{contract_id}/health")
    data = resp.json()
    # 40 (100% complete) + 35 (no overdue) + 15 (no upcoming) + 10 (no risk) = 100
    assert data["score"] == 100.0


def test_overdue_reduces_score(client):
    contract_id = _create_contract(client)
    _add_obligation(client, contract_id, "Overdue 1", status="overdue")
    _add_obligation(client, contract_id, "Pending 1")

    resp = client.get(f"/api/v1/contracts/{contract_id}/health")
    data = resp.json()
    assert data["score"] < 100.0
    assert data["overdue_count"] == 1
    # completion: 0/2 = 0, overdue: 35-10=25, density: 15, risk: 10 = 50
    assert data["breakdown"]["overdue_penalty"] == 25.0


def test_critical_overdue_extra_penalty(client):
    contract_id = _create_contract(client)
    _add_obligation(client, contract_id, "Critical Overdue", status="overdue", risk_level="critical")

    resp = client.get(f"/api/v1/contracts/{contract_id}/health")
    data = resp.json()
    # Risk exposure: 10 - 5 = 5
    assert data["breakdown"]["risk"] == 5.0


def test_waived_excluded_from_denominator(client):
    contract_id = _create_contract(client)
    _add_obligation(client, contract_id, "Completed", status="completed")
    _add_obligation(client, contract_id, "Waived", status="waived")

    resp = client.get(f"/api/v1/contracts/{contract_id}/health")
    data = resp.json()
    # 1 completed out of 1 effective (waived excluded) = 100% completion = 40 points
    assert data["breakdown"]["completion"] == 40.0
