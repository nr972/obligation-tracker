"""Contract CRUD operations."""

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from ot_app.models.contract import Contract
from ot_app.models.obligation import Obligation
from ot_app.schemas.common import ObligationStatus
from ot_app.schemas.contract import ContractCreate, ContractUpdate


def list_contracts(
    db: Session,
    *,
    status: str | None = None,
    contract_type: str | None = None,
    search: str | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[dict]:
    """List contracts with obligation counts."""
    query = db.query(Contract)

    if status:
        query = query.filter(Contract.status == status)
    if contract_type:
        query = query.filter(Contract.contract_type == contract_type)
    if search:
        pattern = f"%{search}%"
        query = query.filter(
            (Contract.title.ilike(pattern)) | (Contract.counterparty.ilike(pattern))
        )

    contracts = query.order_by(Contract.created_at.desc()).offset(skip).limit(limit).all()

    results = []
    for c in contracts:
        ob_count = db.query(func.count(Obligation.id)).filter(Obligation.contract_id == c.id).scalar() or 0
        overdue = (
            db.query(func.count(Obligation.id))
            .filter(Obligation.contract_id == c.id, Obligation.status == ObligationStatus.OVERDUE)
            .scalar()
            or 0
        )
        results.append({
            **{col.name: getattr(c, col.name) for col in c.__table__.columns},
            "obligation_count": ob_count,
            "overdue_count": overdue,
        })
    return results


def get_contract(db: Session, contract_id: int) -> Contract:
    """Get a single contract or raise 404."""
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found.")
    return contract


def get_contract_detail(db: Session, contract_id: int) -> dict:
    """Get contract with obligation counts and obligation list."""
    contract = get_contract(db, contract_id)
    obligations = (
        db.query(Obligation)
        .filter(Obligation.contract_id == contract_id)
        .order_by(Obligation.next_due_date.asc().nullslast())
        .all()
    )
    ob_count = len(obligations)
    overdue = sum(1 for o in obligations if o.status == ObligationStatus.OVERDUE)

    ob_summaries = []
    for o in obligations:
        ob_summaries.append({
            **{col.name: getattr(o, col.name) for col in o.__table__.columns},
            "contract_title": contract.title,
        })

    return {
        **{col.name: getattr(contract, col.name) for col in contract.__table__.columns},
        "obligation_count": ob_count,
        "overdue_count": overdue,
        "obligations": ob_summaries,
    }


def create_contract(db: Session, data: ContractCreate) -> Contract:
    """Create a new contract (no file upload)."""
    contract = Contract(
        **data.model_dump(),
        extraction_status="manual",
    )
    db.add(contract)
    db.commit()
    db.refresh(contract)
    return contract


def update_contract(db: Session, contract_id: int, data: ContractUpdate) -> Contract:
    """Update contract metadata."""
    contract = get_contract(db, contract_id)
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(contract, key, value)
    db.commit()
    db.refresh(contract)
    return contract


def delete_contract(db: Session, contract_id: int) -> None:
    """Delete a contract and its obligations."""
    contract = get_contract(db, contract_id)
    db.delete(contract)
    db.commit()
