"""Obligation CRUD, status management, and overdue detection."""

from datetime import UTC, date, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from ot_app.models.contract import Contract
from ot_app.models.obligation import Obligation
from ot_app.models.status_history import StatusHistory
from ot_app.schemas.common import ExtractionSource, ObligationStatus
from ot_app.schemas.obligation import ObligationCreate, ObligationUpdate, StatusChange


def list_obligations(
    db: Session,
    *,
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
) -> list[dict]:
    """List obligations with filters."""
    query = db.query(Obligation)

    if contract_id:
        query = query.filter(Obligation.contract_id == contract_id)
    if status:
        query = query.filter(Obligation.status == status)
    if obligation_type:
        query = query.filter(Obligation.obligation_type == obligation_type)
    if responsible_party:
        query = query.filter(Obligation.responsible_party == responsible_party)
    if risk_level:
        query = query.filter(Obligation.risk_level == risk_level)
    if due_before:
        query = query.filter(Obligation.next_due_date <= due_before)
    if due_after:
        query = query.filter(Obligation.next_due_date >= due_after)
    if overdue_only:
        query = query.filter(Obligation.status == ObligationStatus.OVERDUE)

    obligations = query.order_by(Obligation.next_due_date.asc().nullslast()).offset(skip).limit(limit).all()

    return [_obligation_to_summary(db, o) for o in obligations]


def get_obligation(db: Session, obligation_id: int) -> Obligation:
    """Get a single obligation or raise 404."""
    obligation = db.query(Obligation).filter(Obligation.id == obligation_id).first()
    if not obligation:
        raise HTTPException(status_code=404, detail="Obligation not found.")
    return obligation


def get_obligation_detail(db: Session, obligation_id: int) -> dict:
    """Get obligation with status history."""
    obligation = get_obligation(db, obligation_id)
    contract = db.query(Contract).filter(Contract.id == obligation.contract_id).first()
    history = (
        db.query(StatusHistory)
        .filter(StatusHistory.obligation_id == obligation_id)
        .order_by(StatusHistory.changed_at.desc())
        .all()
    )

    return {
        **{col.name: getattr(obligation, col.name) for col in obligation.__table__.columns},
        "contract_title": contract.title if contract else "",
        "status_history": [
            {col.name: getattr(h, col.name) for col in h.__table__.columns}
            for h in history
        ],
    }


def create_obligation(db: Session, data: ObligationCreate) -> Obligation:
    """Create an obligation manually."""
    # Verify contract exists
    contract = db.query(Contract).filter(Contract.id == data.contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found.")

    obligation = Obligation(
        **data.model_dump(),
        extraction_source=ExtractionSource.MANUAL,
        next_due_date=data.deadline_date,
    )
    db.add(obligation)
    db.commit()
    db.refresh(obligation)
    return obligation


def update_obligation(db: Session, obligation_id: int, data: ObligationUpdate) -> Obligation:
    """Update obligation fields."""
    obligation = get_obligation(db, obligation_id)
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(obligation, key, value)

    # Sync next_due_date if deadline_date changed
    if "deadline_date" in update_data:
        obligation.next_due_date = update_data["deadline_date"]

    db.commit()
    db.refresh(obligation)
    return obligation


def delete_obligation(db: Session, obligation_id: int) -> None:
    """Delete an obligation."""
    obligation = get_obligation(db, obligation_id)
    db.delete(obligation)
    db.commit()


def change_status(db: Session, obligation_id: int, data: StatusChange) -> Obligation:
    """Change obligation status with audit trail."""
    obligation = get_obligation(db, obligation_id)
    old_status = obligation.status

    if old_status == data.new_status:
        return obligation

    # Record history
    history = StatusHistory(
        obligation_id=obligation_id,
        old_status=old_status,
        new_status=data.new_status,
        notes=data.notes,
    )
    db.add(history)

    obligation.status = data.new_status

    if data.new_status == ObligationStatus.COMPLETED:
        obligation.completed_at = datetime.now(UTC)
    elif old_status == ObligationStatus.COMPLETED:
        obligation.completed_at = None

    db.commit()
    db.refresh(obligation)
    return obligation


def get_upcoming(db: Session, days: int = 30) -> list[dict]:
    """Get obligations due within the next N days."""
    today = date.today()
    cutoff = today + timedelta(days=days)
    obligations = (
        db.query(Obligation)
        .filter(
            Obligation.next_due_date >= today,
            Obligation.next_due_date <= cutoff,
            Obligation.status.in_([
                ObligationStatus.PENDING,
                ObligationStatus.IN_PROGRESS,
            ]),
        )
        .order_by(Obligation.next_due_date.asc())
        .all()
    )
    return [_obligation_to_summary(db, o) for o in obligations]


def get_overdue(db: Session) -> list[dict]:
    """Get all overdue obligations."""
    obligations = (
        db.query(Obligation)
        .filter(Obligation.status == ObligationStatus.OVERDUE)
        .order_by(Obligation.next_due_date.asc())
        .all()
    )
    return [_obligation_to_summary(db, o) for o in obligations]


def get_calendar_events(
    db: Session, start_date: date | None = None, end_date: date | None = None
) -> list[dict]:
    """Get obligations formatted for calendar display."""
    query = db.query(Obligation).filter(Obligation.next_due_date.isnot(None))

    if start_date:
        query = query.filter(Obligation.next_due_date >= start_date)
    if end_date:
        query = query.filter(Obligation.next_due_date <= end_date)

    obligations = query.all()

    risk_colors = {
        "critical": "#dc2626",
        "high": "#ea580c",
        "medium": "#2563eb",
        "low": "#16a34a",
    }
    # Override color for overdue
    overdue_color = "#7f1d1d"

    events = []
    for o in obligations:
        contract = db.query(Contract).filter(Contract.id == o.contract_id).first()
        color = overdue_color if o.status == ObligationStatus.OVERDUE else risk_colors.get(o.risk_level, "#2563eb")
        events.append({
            "id": o.id,
            "title": o.title,
            "start": o.next_due_date.isoformat(),
            "end": o.next_due_date.isoformat(),
            "color": color,
            "contract_title": contract.title if contract else "",
            "obligation_type": o.obligation_type,
            "status": o.status,
            "risk_level": o.risk_level,
        })
    return events


def check_and_update_overdue(db: Session) -> int:
    """Mark pending/in_progress obligations past their due date as overdue."""
    today = date.today()
    overdue_obligations = (
        db.query(Obligation)
        .filter(
            Obligation.next_due_date < today,
            Obligation.status.in_([ObligationStatus.PENDING, ObligationStatus.IN_PROGRESS]),
        )
        .all()
    )

    count = 0
    for o in overdue_obligations:
        history = StatusHistory(
            obligation_id=o.id,
            old_status=o.status,
            new_status=ObligationStatus.OVERDUE,
            notes="Automatically marked overdue by system.",
        )
        db.add(history)
        o.status = ObligationStatus.OVERDUE
        count += 1

    if count:
        db.commit()
    return count


def _obligation_to_summary(db: Session, o: Obligation) -> dict:
    """Convert obligation ORM object to summary dict with contract_title."""
    contract = db.query(Contract).filter(Contract.id == o.contract_id).first()
    return {
        **{col.name: getattr(o, col.name) for col in o.__table__.columns},
        "contract_title": contract.title if contract else "",
    }
