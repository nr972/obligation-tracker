"""Health score computation for contracts."""

from datetime import date, timedelta

from sqlalchemy.orm import Session

from ot_app.models.contract import Contract
from ot_app.models.obligation import Obligation
from ot_app.schemas.common import ObligationStatus, RiskLevel
from ot_app.schemas.dashboard import HealthScore


def compute_health_score(db: Session, contract_id: int) -> HealthScore:
    """Compute and store health score for a contract.

    Formula (weights sum to 100):
    - Completion rate: 40 — (completed / total) * 40
    - Overdue penalty: 35 — max(0, 35 - overdue_count * 10)
    - Upcoming density: 15 — 15 - min(15, upcoming_30d * 2)
    - Risk exposure: 10 — 10 - (critical_overdue * 5 + high_overdue * 3)
    """
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise ValueError(f"Contract {contract_id} not found")

    obligations = (
        db.query(Obligation).filter(Obligation.contract_id == contract_id).all()
    )
    total = len(obligations)

    if total == 0:
        score_data = HealthScore(
            contract_id=contract_id,
            contract_title=contract.title,
            score=100.0,
            completed_count=0,
            total_count=0,
            overdue_count=0,
            upcoming_density=0,
            breakdown={"completion": 40.0, "overdue_penalty": 35.0, "density": 15.0, "risk": 10.0},
        )
        contract.health_score = 100.0
        db.commit()
        return score_data

    completed = sum(1 for o in obligations if o.status == ObligationStatus.COMPLETED)
    overdue = sum(1 for o in obligations if o.status == ObligationStatus.OVERDUE)
    waived = sum(1 for o in obligations if o.status == ObligationStatus.WAIVED)

    today = date.today()
    cutoff_30 = today + timedelta(days=30)
    upcoming_30 = sum(
        1
        for o in obligations
        if o.next_due_date
        and today <= o.next_due_date <= cutoff_30
        and o.status in (ObligationStatus.PENDING, ObligationStatus.IN_PROGRESS)
    )

    critical_overdue = sum(
        1 for o in obligations
        if o.status == ObligationStatus.OVERDUE and o.risk_level == RiskLevel.CRITICAL
    )
    high_overdue = sum(
        1 for o in obligations
        if o.status == ObligationStatus.OVERDUE and o.risk_level == RiskLevel.HIGH
    )

    # Denominator excludes waived obligations
    effective_total = total - waived
    if effective_total == 0:
        effective_total = 1  # avoid division by zero

    completion_score = (completed / effective_total) * 40.0
    overdue_score = max(0.0, 35.0 - overdue * 10.0)
    density_score = 15.0 - min(15.0, upcoming_30 * 2.0)
    risk_score = max(0.0, 10.0 - (critical_overdue * 5.0 + high_overdue * 3.0))

    total_score = max(0.0, min(100.0, completion_score + overdue_score + density_score + risk_score))

    contract.health_score = round(total_score, 1)
    db.commit()

    return HealthScore(
        contract_id=contract_id,
        contract_title=contract.title,
        score=round(total_score, 1),
        completed_count=completed,
        total_count=total,
        overdue_count=overdue,
        upcoming_density=upcoming_30,
        breakdown={
            "completion": round(completion_score, 1),
            "overdue_penalty": round(overdue_score, 1),
            "density": round(density_score, 1),
            "risk": round(risk_score, 1),
        },
    )
