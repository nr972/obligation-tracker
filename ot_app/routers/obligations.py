"""Obligation API endpoints."""

from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ot_app.database import get_db
from ot_app.schemas.dashboard import CalendarEvent
from ot_app.schemas.obligation import (
    ObligationCreate,
    ObligationDetail,
    ObligationSummary,
    StatusChange,
)
from ot_app.services import obligation_service, scoring_service

router = APIRouter(prefix="/obligations", tags=["obligations"])


@router.get("", response_model=list[ObligationSummary])
def list_obligations(
    contract_id: int | None = None,
    status: str | None = None,
    obligation_type: str | None = None,
    responsible_party: str | None = None,
    risk_level: str | None = None,
    due_before: date | None = None,
    due_after: date | None = None,
    overdue_only: bool = False,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    return obligation_service.list_obligations(
        db,
        contract_id=contract_id,
        status=status,
        obligation_type=obligation_type,
        responsible_party=responsible_party,
        risk_level=risk_level,
        due_before=due_before,
        due_after=due_after,
        overdue_only=overdue_only,
        skip=skip,
        limit=limit,
    )


@router.post("", response_model=ObligationDetail, status_code=201)
def create_obligation(data: ObligationCreate, db: Session = Depends(get_db)):
    obligation = obligation_service.create_obligation(db, data)
    # Recompute health score
    scoring_service.compute_health_score(db, obligation.contract_id)
    return obligation_service.get_obligation_detail(db, obligation.id)


@router.get("/upcoming", response_model=list[ObligationSummary])
def get_upcoming(days: int = 30, db: Session = Depends(get_db)):
    return obligation_service.get_upcoming(db, days=days)


@router.get("/overdue", response_model=list[ObligationSummary])
def get_overdue(db: Session = Depends(get_db)):
    return obligation_service.get_overdue(db)


@router.get("/calendar", response_model=list[CalendarEvent])
def get_calendar_events(
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
):
    return obligation_service.get_calendar_events(db, start_date=start_date, end_date=end_date)


@router.get("/{obligation_id}", response_model=ObligationDetail)
def get_obligation(obligation_id: int, db: Session = Depends(get_db)):
    return obligation_service.get_obligation_detail(db, obligation_id)


@router.put("/{obligation_id}", response_model=ObligationDetail)
def update_obligation(obligation_id: int, data: ObligationCreate, db: Session = Depends(get_db)):
    from ot_app.schemas.obligation import ObligationUpdate

    update_data = ObligationUpdate(**data.model_dump(exclude={"contract_id"}))
    obligation = obligation_service.update_obligation(db, obligation_id, update_data)
    scoring_service.compute_health_score(db, obligation.contract_id)
    return obligation_service.get_obligation_detail(db, obligation_id)


@router.delete("/{obligation_id}", status_code=204)
def delete_obligation(obligation_id: int, db: Session = Depends(get_db)):
    obligation = obligation_service.get_obligation(db, obligation_id)
    contract_id = obligation.contract_id
    obligation_service.delete_obligation(db, obligation_id)
    scoring_service.compute_health_score(db, contract_id)


@router.patch("/{obligation_id}/status", response_model=ObligationDetail)
def change_status(obligation_id: int, data: StatusChange, db: Session = Depends(get_db)):
    obligation = obligation_service.change_status(db, obligation_id, data)
    scoring_service.compute_health_score(db, obligation.contract_id)
    return obligation_service.get_obligation_detail(db, obligation_id)
