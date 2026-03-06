"""Contract request/response schemas."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from ot_app.schemas.common import ContractStatus, ContractType, ExtractionStatus, RenewalType


class ContractCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    counterparty: str = Field(..., min_length=1, max_length=500)
    contract_type: ContractType
    effective_date: date | None = None
    expiration_date: date | None = None
    renewal_type: RenewalType | None = None
    notice_period_days: int | None = Field(None, ge=0)


class ContractUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=500)
    counterparty: str | None = Field(None, min_length=1, max_length=500)
    contract_type: ContractType | None = None
    effective_date: date | None = None
    expiration_date: date | None = None
    renewal_type: RenewalType | None = None
    notice_period_days: int | None = Field(None, ge=0)
    status: ContractStatus | None = None


class ContractSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    counterparty: str
    contract_type: str
    effective_date: date | None
    expiration_date: date | None
    status: str
    health_score: float | None
    obligation_count: int = 0
    overdue_count: int = 0
    extraction_status: str
    is_sample: bool
    created_at: datetime


class ContractDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    counterparty: str
    contract_type: str
    effective_date: date | None
    expiration_date: date | None
    renewal_type: str | None
    notice_period_days: int | None
    file_name: str | None
    file_type: str | None
    file_size_bytes: int | None
    status: str
    health_score: float | None
    extraction_status: str
    is_sample: bool
    obligation_count: int = 0
    overdue_count: int = 0
    obligations: list["ObligationSummary"] = []
    created_at: datetime
    updated_at: datetime


# Avoid circular import
from ot_app.schemas.obligation import ObligationSummary  # noqa: E402

ContractDetail.model_rebuild()
