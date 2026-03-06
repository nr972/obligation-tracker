"""AI extraction pipeline: parse document → detect sections → extract obligations."""

import json
import logging

from sqlalchemy.orm import Session

from ot_app.config import settings
from ot_app.models.contract import Contract
from ot_app.models.obligation import Obligation
from ot_app.schemas.common import (
    DeadlineType,
    ExtractionSource,
    ExtractionStatus,
    ObligationType,
    ResponsibleParty,
    RiskLevel,
)
from ot_app.schemas.extraction import ExtractionResult
from ot_app.services.scoring_service import compute_health_score
from ot_app.utils.document_parser import parse_document
from ot_app.utils.prompts import EXTRACTION_SYSTEM_PROMPT, build_extraction_prompt
from ot_app.utils.section_detector import filter_obligation_sections, detect_sections

logger = logging.getLogger(__name__)

# Valid enum values for validation
VALID_OBLIGATION_TYPES = {e.value for e in ObligationType}
VALID_RESPONSIBLE_PARTIES = {e.value for e in ResponsibleParty}
VALID_DEADLINE_TYPES = {e.value for e in DeadlineType}
VALID_RISK_LEVELS = {e.value for e in RiskLevel}


def extract_obligations(contract_id: int, db: Session) -> ExtractionResult:
    """Run the full extraction pipeline on a contract."""
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Contract not found.")

    if not contract.file_path:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="No file uploaded for this contract.")

    # Mark as processing
    contract.extraction_status = ExtractionStatus.PROCESSING
    db.commit()

    try:
        # Step 1: Parse document
        text = parse_document(contract.file_path)

        # Step 2: Detect and filter sections
        sections = detect_sections(text)
        relevant_sections = filter_obligation_sections(sections)

        # Step 3: Extract obligations from each section via Claude
        import anthropic

        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        all_obligations = []

        for section in relevant_sections:
            user_prompt = build_extraction_prompt(
                section_heading=section.heading,
                section_content=section.content,
                counterparty=contract.counterparty,
                contract_type=contract.contract_type,
            )

            try:
                response = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=4096,
                    system=EXTRACTION_SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": user_prompt}],
                )

                response_text = response.content[0].text.strip()
                # Strip markdown code fences if present
                if response_text.startswith("```"):
                    response_text = response_text.split("\n", 1)[1]
                    if response_text.endswith("```"):
                        response_text = response_text[:-3]

                parsed = json.loads(response_text)
                if not isinstance(parsed, list):
                    parsed = [parsed]

                for raw_ob in parsed:
                    obligation = _validate_and_create_obligation(
                        raw_ob, contract_id, section.heading, section.content, db
                    )
                    if obligation:
                        all_obligations.append(obligation)

            except (json.JSONDecodeError, anthropic.APIError) as e:
                logger.warning(
                    "Extraction failed for section '%s': %s", section.heading, str(e)
                )
                continue

        # Step 4: Update contract status
        contract.extraction_status = ExtractionStatus.COMPLETED
        db.commit()

        # Step 5: Recompute health score
        compute_health_score(db, contract_id)

        # Build summary response
        ob_summaries = []
        for ob in all_obligations:
            ob_summaries.append({
                **{col.name: getattr(ob, col.name) for col in ob.__table__.columns},
                "contract_title": contract.title,
            })

        return ExtractionResult(
            contract_id=contract_id,
            obligations_found=len(all_obligations),
            obligations=ob_summaries,
            extraction_source="ai",
            sections_processed=len(relevant_sections),
        )

    except Exception as e:
        contract.extraction_status = ExtractionStatus.FAILED
        db.commit()
        logger.error("Extraction failed for contract %d: %s", contract_id, str(e))
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail="Extraction failed. Please try again.")


def _validate_and_create_obligation(
    raw: dict,
    contract_id: int,
    section_heading: str,
    section_content: str,
    db: Session,
) -> Obligation | None:
    """Validate extracted obligation data and create DB record."""
    try:
        title = str(raw.get("title", ""))[:500]
        if not title:
            return None

        ob_type = raw.get("obligation_type", "other")
        if ob_type not in VALID_OBLIGATION_TYPES:
            ob_type = "other"

        responsible = raw.get("responsible_party", "both")
        if responsible not in VALID_RESPONSIBLE_PARTIES:
            responsible = "both"

        deadline_type = raw.get("deadline_type", "ongoing")
        if deadline_type not in VALID_DEADLINE_TYPES:
            deadline_type = "ongoing"

        risk_level = raw.get("risk_level", "medium")
        if risk_level not in VALID_RISK_LEVELS:
            risk_level = "medium"

        deadline_date = None
        raw_date = raw.get("deadline_date")
        if raw_date and isinstance(raw_date, str):
            try:
                from datetime import date
                deadline_date = date.fromisoformat(raw_date)
            except ValueError:
                pass

        recurrence = raw.get("recurrence_pattern")
        if recurrence not in ("weekly", "monthly", "quarterly", "annually"):
            recurrence = None

        obligation = Obligation(
            contract_id=contract_id,
            title=title,
            description=str(raw.get("description", ""))[:5000] or None,
            obligation_type=ob_type,
            responsible_party=responsible,
            deadline_type=deadline_type,
            deadline_date=deadline_date,
            recurrence_pattern=recurrence,
            next_due_date=deadline_date,
            penalty=str(raw.get("penalty", ""))[:2000] or None,
            risk_level=risk_level,
            extraction_source=ExtractionSource.AI,
            source_section=section_heading[:200],
            source_text=section_content[:2000],
        )
        db.add(obligation)
        db.commit()
        db.refresh(obligation)
        return obligation

    except Exception as e:
        logger.warning("Failed to create obligation from extraction: %s", str(e))
        db.rollback()
        return None
