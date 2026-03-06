"""Dashboard and analytics endpoints."""

from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ot_app.database import get_db
from ot_app.models.contract import Contract
from ot_app.models.obligation import Obligation
from ot_app.schemas.common import ObligationStatus
from ot_app.schemas.dashboard import ContractHealthSummary, DashboardSummary

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def get_summary(db: Session = Depends(get_db)):
    total_contracts = db.query(func.count(Contract.id)).scalar() or 0
    total_obligations = db.query(func.count(Obligation.id)).scalar() or 0
    overdue_count = (
        db.query(func.count(Obligation.id))
        .filter(Obligation.status == ObligationStatus.OVERDUE)
        .scalar()
        or 0
    )

    today = date.today()
    upcoming_7 = (
        db.query(func.count(Obligation.id))
        .filter(
            Obligation.next_due_date >= today,
            Obligation.next_due_date <= today + timedelta(days=7),
            Obligation.status.in_([ObligationStatus.PENDING, ObligationStatus.IN_PROGRESS]),
        )
        .scalar()
        or 0
    )
    upcoming_30 = (
        db.query(func.count(Obligation.id))
        .filter(
            Obligation.next_due_date >= today,
            Obligation.next_due_date <= today + timedelta(days=30),
            Obligation.status.in_([ObligationStatus.PENDING, ObligationStatus.IN_PROGRESS]),
        )
        .scalar()
        or 0
    )

    avg_score = db.query(func.avg(Contract.health_score)).filter(Contract.health_score.isnot(None)).scalar()
    avg_health = round(avg_score, 1) if avg_score is not None else None

    # Status breakdown
    status_rows = (
        db.query(Obligation.status, func.count(Obligation.id))
        .group_by(Obligation.status)
        .all()
    )
    status_breakdown = {row[0]: row[1] for row in status_rows}

    # Type breakdown
    type_rows = (
        db.query(Obligation.obligation_type, func.count(Obligation.id))
        .group_by(Obligation.obligation_type)
        .all()
    )
    type_breakdown = {row[0]: row[1] for row in type_rows}

    return DashboardSummary(
        total_contracts=total_contracts,
        total_obligations=total_obligations,
        overdue_count=overdue_count,
        upcoming_7_days=upcoming_7,
        upcoming_30_days=upcoming_30,
        avg_health_score=avg_health,
        status_breakdown=status_breakdown,
        type_breakdown=type_breakdown,
    )


@router.get("/health-scores", response_model=list[ContractHealthSummary])
def get_health_scores(db: Session = Depends(get_db)):
    contracts = db.query(Contract).order_by(Contract.health_score.asc().nullslast()).all()
    results = []
    for c in contracts:
        ob_count = db.query(func.count(Obligation.id)).filter(Obligation.contract_id == c.id).scalar() or 0
        overdue = (
            db.query(func.count(Obligation.id))
            .filter(Obligation.contract_id == c.id, Obligation.status == ObligationStatus.OVERDUE)
            .scalar()
            or 0
        )
        results.append(ContractHealthSummary(
            id=c.id,
            title=c.title,
            counterparty=c.counterparty,
            contract_type=c.contract_type,
            status=c.status,
            health_score=c.health_score,
            obligation_count=ob_count,
            overdue_count=overdue,
        ))
    return results
