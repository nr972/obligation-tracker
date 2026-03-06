"""File upload validation, sanitization, and storage."""

import re
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile

from ot_app.config import settings

ALLOWED_EXTENSIONS = {".pdf", ".docx"}
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def sanitize_filename(filename: str) -> str:
    """Remove path components and dangerous characters from filename."""
    # Strip any path components
    name = Path(filename).name
    # Remove anything that isn't alphanumeric, dash, underscore, dot, or space
    name = re.sub(r"[^\w\s\-.]", "", name)
    # Collapse whitespace
    name = re.sub(r"\s+", "_", name.strip())
    if not name:
        name = "unnamed"
    return name


def validate_file(file: UploadFile) -> None:
    """Validate file type and size. Raises HTTPException on failure."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{ext}' not allowed. Accepted: PDF, DOCX.",
        )

    if file.content_type and file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Invalid content type. Accepted: PDF, DOCX.",
        )


async def save_upload(file: UploadFile) -> tuple[str, str, int, str]:
    """Save uploaded file to disk. Returns (stored_path, original_name, size_bytes, file_type)."""
    validate_file(file)

    original_name = sanitize_filename(file.filename or "unnamed")
    ext = Path(original_name).suffix.lower()
    stored_name = f"{uuid.uuid4().hex}{ext}"
    stored_path = settings.upload_path / stored_name

    content = await file.read()
    size = len(content)

    if size > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({size / 1024 / 1024:.1f} MB). Maximum: {settings.MAX_FILE_SIZE_MB} MB.",
        )

    if size == 0:
        raise HTTPException(status_code=400, detail="File is empty.")

    stored_path.write_bytes(content)

    file_type = ext.lstrip(".")
    return str(stored_path), original_name, size, file_type
