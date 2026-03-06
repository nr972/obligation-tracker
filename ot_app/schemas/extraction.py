"""Extraction result schemas."""

from pydantic import BaseModel

from ot_app.schemas.obligation import ObligationSummary


class ExtractionResult(BaseModel):
    contract_id: int
    obligations_found: int
    obligations: list[ObligationSummary]
    extraction_source: str
    sections_processed: int
