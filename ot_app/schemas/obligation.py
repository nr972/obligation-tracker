"""Obligation request/response schemas."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from ot_app.schemas.common import (
    DeadlineType,
    ExtractionSource,
    ObligationStatus,
    ObligationType,
    RecurrencePattern,
    ResponsibleParty,
    RiskLevel,
)


class ObligationCreate(BaseModel):
    contract_id: int
    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    obligation_type: ObligationType
    responsible_party: ResponsibleParty
    deadline_type: DeadlineType
    deadline_date: date | None = None
    recurrence_pattern: RecurrencePattern | None = None
    penalty: str | None = None
    risk_level: RiskLevel = RiskLevel.MEDIUM
    notes: str | None = None


class ObligationUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=500)
    description: str | None = None
    obligation_type: ObligationType | None = None
    responsible_party: ResponsibleParty | None = None
    deadline_type: DeadlineType | None = None
    deadline_date: date | None = None
    recurrence_pattern: RecurrencePattern | None = None
    penalty: str | None = None
    risk_level: RiskLevel | None = None
    notes: str | None = None


class StatusChange(BaseModel):
    new_status: ObligationStatus
    notes: str | None = None


class StatusHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    old_status: str
    new_status: str
    changed_at: datetime
    notes: str | None


class ObligationSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    contract_id: int
    contract_title: str = ""
    title: str
    obligation_type: str
    responsible_party: str
    deadline_type: str
    deadline_date: date | None
    next_due_date: date | None
    risk_level: str
    status: str
    extraction_source: str
    created_at: datetime


class ObligationDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    contract_id: int
    contract_title: str = ""
    title: str
    description: str | None
    obligation_type: str
    responsible_party: str
    deadline_type: str
    deadline_date: date | None
    recurrence_pattern: str | None
    next_due_date: date | None
    penalty: str | None
    risk_level: str
    status: str
    extraction_source: str
    source_section: str | None
    source_text: str | None
    notes: str | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    status_history: list[StatusHistoryItem] = []
