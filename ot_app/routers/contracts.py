"""Contract API endpoints."""

from fastapi import APIRouter, Depends, Form, UploadFile
from sqlalchemy.orm import Session

from ot_app.config import settings
from ot_app.database import get_db
from ot_app.schemas.common import ContractType
from ot_app.schemas.contract import ContractCreate, ContractDetail, ContractSummary, ContractUpdate
from ot_app.schemas.dashboard import HealthScore
from ot_app.schemas.extraction import ExtractionResult
from ot_app.services import contract_service, scoring_service

router = APIRouter(prefix="/contracts", tags=["contracts"])


@router.get("", response_model=list[ContractSummary])
def list_contracts(
    status: str | None = None,
    contract_type: str | None = None,
    search: str | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    results = contract_service.list_contracts(
        db, status=status, contract_type=contract_type, search=search, skip=skip, limit=limit
    )
    return results


@router.post("", response_model=ContractDetail, status_code=201)
def create_contract(data: ContractCreate, db: Session = Depends(get_db)):
    contract = contract_service.create_contract(db, data)
    return contract_service.get_contract_detail(db, contract.id)


@router.get("/{contract_id}", response_model=ContractDetail)
def get_contract(contract_id: int, db: Session = Depends(get_db)):
    return contract_service.get_contract_detail(db, contract_id)


@router.put("/{contract_id}", response_model=ContractDetail)
def update_contract(contract_id: int, data: ContractUpdate, db: Session = Depends(get_db)):
    contract_service.update_contract(db, contract_id, data)
    return contract_service.get_contract_detail(db, contract_id)


@router.delete("/{contract_id}", status_code=204)
def delete_contract(contract_id: int, db: Session = Depends(get_db)):
    contract_service.delete_contract(db, contract_id)


@router.post("/upload", response_model=ContractDetail, status_code=201)
async def upload_contract(
    file: UploadFile,
    title: str = Form(...),
    counterparty: str = Form(...),
    contract_type: ContractType = Form(...),
    db: Session = Depends(get_db),
):
    from ot_app.utils.file_handler import save_upload

    stored_path, original_name, size, file_type = await save_upload(file)

    from ot_app.models.contract import Contract

    contract = Contract(
        title=title,
        counterparty=counterparty,
        contract_type=contract_type,
        file_path=stored_path,
        file_name=original_name,
        file_size_bytes=size,
        file_type=file_type,
        extraction_status="pending",
    )
    db.add(contract)
    db.commit()
    db.refresh(contract)

    return contract_service.get_contract_detail(db, contract.id)


@router.post("/{contract_id}/extract", response_model=ExtractionResult)
def extract_obligations(contract_id: int, db: Session = Depends(get_db)):
    if not settings.ai_enabled:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=503,
            detail="AI extraction not available. Set ANTHROPIC_API_KEY environment variable.",
        )

    from ot_app.services.extraction_service import extract_obligations as do_extract

    return do_extract(contract_id, db)


@router.get("/{contract_id}/health", response_model=HealthScore)
def get_health_score(contract_id: int, db: Session = Depends(get_db)):
    return scoring_service.compute_health_score(db, contract_id)
