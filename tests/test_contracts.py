"""Tests for contract CRUD endpoints."""


def test_health_check(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


def test_create_contract(client):
    resp = client.post("/api/v1/contracts", json={
        "title": "Test SaaS Agreement",
        "counterparty": "Acme Corp",
        "contract_type": "saas",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Test SaaS Agreement"
    assert data["counterparty"] == "Acme Corp"
    assert data["extraction_status"] == "manual"
    assert data["obligation_count"] == 0


def test_list_contracts(client):
    # Create two contracts
    client.post("/api/v1/contracts", json={
        "title": "Contract A",
        "counterparty": "Company A",
        "contract_type": "vendor",
    })
    client.post("/api/v1/contracts", json={
        "title": "Contract B",
        "counterparty": "Company B",
        "contract_type": "dpa",
    })
    resp = client.get("/api/v1/contracts")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2


def test_get_contract(client):
    create_resp = client.post("/api/v1/contracts", json={
        "title": "Detail Test",
        "counterparty": "Detail Corp",
        "contract_type": "consulting",
    })
    contract_id = create_resp.json()["id"]

    resp = client.get(f"/api/v1/contracts/{contract_id}")
    assert resp.status_code == 200
    assert resp.json()["title"] == "Detail Test"


def test_update_contract(client):
    create_resp = client.post("/api/v1/contracts", json={
        "title": "Original Title",
        "counterparty": "Original Corp",
        "contract_type": "msa",
    })
    contract_id = create_resp.json()["id"]

    resp = client.put(f"/api/v1/contracts/{contract_id}", json={
        "title": "Updated Title",
    })
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated Title"


def test_delete_contract(client):
    create_resp = client.post("/api/v1/contracts", json={
        "title": "To Delete",
        "counterparty": "Delete Corp",
        "contract_type": "lease",
    })
    contract_id = create_resp.json()["id"]

    resp = client.delete(f"/api/v1/contracts/{contract_id}")
    assert resp.status_code == 204

    resp = client.get(f"/api/v1/contracts/{contract_id}")
    assert resp.status_code == 404


def test_contract_not_found(client):
    resp = client.get("/api/v1/contracts/9999")
    assert resp.status_code == 404


def test_search_contracts(client):
    client.post("/api/v1/contracts", json={
        "title": "Alpha Agreement",
        "counterparty": "Alpha Inc",
        "contract_type": "saas",
    })
    client.post("/api/v1/contracts", json={
        "title": "Beta Agreement",
        "counterparty": "Beta LLC",
        "contract_type": "vendor",
    })

    resp = client.get("/api/v1/contracts?search=Alpha")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["counterparty"] == "Alpha Inc"


def test_filter_by_type(client):
    client.post("/api/v1/contracts", json={
        "title": "SaaS Contract",
        "counterparty": "SaaS Corp",
        "contract_type": "saas",
    })
    client.post("/api/v1/contracts", json={
        "title": "DPA Contract",
        "counterparty": "DPA Corp",
        "contract_type": "dpa",
    })

    resp = client.get("/api/v1/contracts?contract_type=saas")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["contract_type"] == "saas"


def test_invalid_contract_type(client):
    resp = client.post("/api/v1/contracts", json={
        "title": "Bad Type",
        "counterparty": "Bad Corp",
        "contract_type": "invalid_type",
    })
    assert resp.status_code == 422
