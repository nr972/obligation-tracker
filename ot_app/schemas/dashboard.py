"""Dashboard and analytics schemas."""

from pydantic import BaseModel, ConfigDict


class DashboardSummary(BaseModel):
    total_contracts: int
    total_obligations: int
    overdue_count: int
    upcoming_7_days: int
    upcoming_30_days: int
    avg_health_score: float | None
    status_breakdown: dict[str, int]
    type_breakdown: dict[str, int]


class HealthScore(BaseModel):
    contract_id: int
    contract_title: str
    score: float
    completed_count: int
    total_count: int
    overdue_count: int
    upcoming_density: int
    breakdown: dict[str, float]


class ContractHealthSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    counterparty: str
    contract_type: str
    status: str
    health_score: float | None
    obligation_count: int = 0
    overdue_count: int = 0


class CalendarEvent(BaseModel):
    id: int
    title: str
    start: str
    end: str
    color: str
    contract_title: str
    obligation_type: str
    status: str
    risk_level: str
