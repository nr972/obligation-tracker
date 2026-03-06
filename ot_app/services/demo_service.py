"""Load and clear sample/demo data."""

import json
from datetime import date, timedelta
from pathlib import Path

from sqlalchemy.orm import Session

from ot_app.models.contract import Contract
from ot_app.models.obligation import Obligation
from ot_app.schemas.common import ExtractionSource, ExtractionStatus

SAMPLE_DIR = Path(__file__).parent.parent.parent / "data" / "sample"


def load_sample_data(db: Session) -> int:
    """Load sample contracts and obligations from JSON. Returns count of obligations loaded."""
    obligations_file = SAMPLE_DIR / "obligations.json"
    if not obligations_file.exists():
        return 0

    with open(obligations_file) as f:
        sample_data = json.load(f)

    total_loaded = 0

    for contract_data in sample_data.get("contracts", []):
        # Check if already loaded
        existing = (
            db.query(Contract)
            .filter(Contract.title == contract_data["title"], Contract.is_sample.is_(True))
            .first()
        )
        if existing:
            continue

        contract = Contract(
            title=contract_data["title"],
            counterparty=contract_data["counterparty"],
            contract_type=contract_data["contract_type"],
            effective_date=_parse_date(contract_data.get("effective_date")),
            expiration_date=_parse_date(contract_data.get("expiration_date")),
            renewal_type=contract_data.get("renewal_type"),
            notice_period_days=contract_data.get("notice_period_days"),
            status="active",
            extraction_status=ExtractionStatus.COMPLETED,
            is_sample=True,
        )
        db.add(contract)
        db.flush()

        for ob_data in contract_data.get("obligations", []):
            # Offset dates relative to today so sample data always looks current
            deadline = _compute_sample_date(ob_data.get("days_from_now"))

            obligation = Obligation(
                contract_id=contract.id,
                title=ob_data["title"],
                description=ob_data.get("description"),
                obligation_type=ob_data["obligation_type"],
                responsible_party=ob_data["responsible_party"],
                deadline_type=ob_data["deadline_type"],
                deadline_date=deadline,
                recurrence_pattern=ob_data.get("recurrence_pattern"),
                next_due_date=deadline,
                penalty=ob_data.get("penalty"),
                risk_level=ob_data.get("risk_level", "medium"),
                status=ob_data.get("status", "pending"),
                extraction_source=ExtractionSource.SAMPLE,
                source_section=ob_data.get("source_section"),
            )
            db.add(obligation)
            total_loaded += 1

    db.commit()

    # Compute health scores for loaded contracts
    from ot_app.services.scoring_service import compute_health_score
    sample_contracts = db.query(Contract).filter(Contract.is_sample.is_(True)).all()
    for c in sample_contracts:
        compute_health_score(db, c.id)

    return total_loaded


def clear_sample_data(db: Session) -> int:
    """Delete all sample contracts and their obligations. Returns count deleted."""
    sample_contracts = db.query(Contract).filter(Contract.is_sample.is_(True)).all()
    count = len(sample_contracts)
    for c in sample_contracts:
        db.delete(c)
    db.commit()
    return count


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _compute_sample_date(days_from_now: int | None) -> date | None:
    if days_from_now is None:
        return None
    return date.today() + timedelta(days=days_from_now)
