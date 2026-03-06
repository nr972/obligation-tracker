"""HTTP client wrapper for FastAPI backend calls."""

import os

import requests

API_BASE = os.getenv("API_URL", "http://localhost:8000") + "/api/v1"


def _url(path: str) -> str:
    return f"{API_BASE}{path}"


def _handle(resp: requests.Response) -> dict | list | None:
    if resp.status_code == 204:
        return None
    resp.raise_for_status()
    return resp.json()


# --- System ---

def get_health() -> dict:
    return _handle(requests.get(_url("/health")))


def get_mode() -> dict:
    return _handle(requests.get(_url("/config/mode")))


def load_demo_data() -> dict:
    return _handle(requests.post(_url("/demo/load")))


def reset_demo_data() -> dict:
    return _handle(requests.post(_url("/demo/reset")))


def request_shutdown() -> dict:
    """Ask the API to shut down the process group. May raise on connection loss."""
    return _handle(requests.post(_url("/shutdown"), timeout=5))


# --- Contracts ---

def list_contracts(status=None, contract_type=None, search=None) -> list:
    params = {}
    if status:
        params["status"] = status
    if contract_type:
        params["contract_type"] = contract_type
    if search:
        params["search"] = search
    return _handle(requests.get(_url("/contracts"), params=params))


def get_contract(contract_id: int) -> dict:
    return _handle(requests.get(_url(f"/contracts/{contract_id}")))


def create_contract(data: dict) -> dict:
    return _handle(requests.post(_url("/contracts"), json=data))


def update_contract(contract_id: int, data: dict) -> dict:
    return _handle(requests.put(_url(f"/contracts/{contract_id}"), json=data))


def delete_contract(contract_id: int) -> None:
    _handle(requests.delete(_url(f"/contracts/{contract_id}")))


def upload_contract(file, title: str, counterparty: str, contract_type: str) -> dict:
    files = {"file": (file.name, file, file.type)}
    data = {"title": title, "counterparty": counterparty, "contract_type": contract_type}
    return _handle(requests.post(_url("/contracts/upload"), files=files, data=data))


def extract_obligations(contract_id: int) -> dict:
    return _handle(requests.post(_url(f"/contracts/{contract_id}/extract")))


def get_health_score(contract_id: int) -> dict:
    return _handle(requests.get(_url(f"/contracts/{contract_id}/health")))


# --- Obligations ---

def list_obligations(**kwargs) -> list:
    params = {k: v for k, v in kwargs.items() if v is not None}
    return _handle(requests.get(_url("/obligations"), params=params))


def get_obligation(obligation_id: int) -> dict:
    return _handle(requests.get(_url(f"/obligations/{obligation_id}")))


def create_obligation(data: dict) -> dict:
    return _handle(requests.post(_url("/obligations"), json=data))


def update_obligation(obligation_id: int, data: dict) -> dict:
    return _handle(requests.put(_url(f"/obligations/{obligation_id}"), json=data))


def delete_obligation(obligation_id: int) -> None:
    _handle(requests.delete(_url(f"/obligations/{obligation_id}")))


def change_obligation_status(obligation_id: int, new_status: str, notes: str | None = None) -> dict:
    data = {"new_status": new_status}
    if notes:
        data["notes"] = notes
    return _handle(requests.patch(_url(f"/obligations/{obligation_id}/status"), json=data))


def get_upcoming(days: int = 30) -> list:
    return _handle(requests.get(_url("/obligations/upcoming"), params={"days": days}))


def get_overdue() -> list:
    return _handle(requests.get(_url("/obligations/overdue")))


def get_calendar_events(start_date=None, end_date=None) -> list:
    params = {}
    if start_date:
        params["start_date"] = str(start_date)
    if end_date:
        params["end_date"] = str(end_date)
    return _handle(requests.get(_url("/obligations/calendar"), params=params))


# --- Dashboard ---

def get_dashboard_summary() -> dict:
    return _handle(requests.get(_url("/dashboard/summary")))


def get_health_scores() -> list:
    return _handle(requests.get(_url("/dashboard/health-scores")))
