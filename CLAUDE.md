# CLAUDE.md — Contract Obligation Tracker

## Project Overview

Contract Obligation Tracker & Compliance Dashboard. Extracts obligations, deadlines, SLAs, renewal dates, and deliverables from executed contracts using AI, stores them in a structured database, and surfaces upcoming obligations via a dashboard with alerts.

See `PROJECT.md` for full requirements and `PORTFOLIO_STANDARDS.md` for cross-portfolio conventions.

## Package Names

This project uses prefixed package names to avoid collisions across the portfolio:
- **Backend:** `ot_app/` (not `app/`)
- **Frontend:** `ot_frontend/` (not `frontend/`)
- Entry points: `uvicorn ot_app.main:app`, `streamlit run ot_frontend/app.py`

## Tech Stack

- Python 3.11+, FastAPI, Pydantic v2
- SQLAlchemy 2.0 (mapped_column, DeclarativeBase) with SQLite (prototype)
- Anthropic API (Claude) for obligation extraction
- Document parsing: python-docx (Word), PyMuPDF/pdfplumber (PDF)
- Streamlit frontend (thin client calling API via HTTP)
- Docker + Railway deployment

## Architecture

**API-first:** All business logic lives in the FastAPI backend. Streamlit is a thin HTTP client only. The API must be independently usable (Swagger docs, curl, integrations).

## Project Structure

```
obligation-tracker/
├── ot_app/                  # FastAPI backend
│   ├── main.py              # App entry point, router mounting
│   ├── config.py            # Settings via pydantic-settings
│   ├── database.py          # SQLAlchemy engine, session, Base
│   ├── models/              # SQLAlchemy ORM models
│   ├── schemas/             # Pydantic request/response schemas
│   ├── routers/             # FastAPI route modules
│   ├── services/            # Business logic (extraction, scoring)
│   └── utils/               # Document parsing, helpers
├── ot_frontend/             # Streamlit frontend
│   └── app.py
├── tests/                   # pytest tests
├── data/sample/             # Synthetic sample contracts
├── pyproject.toml           # PEP 621 package config
├── start.sh / start.bat     # One-command launch scripts
├── Dockerfile               # API container
├── docker-compose.yml       # Multi-service orchestration
├── Dockerfile.railway       # Single-container cloud deploy
├── railway.json             # Railway config
├── railway_start.sh         # Railway startup script
└── README.md
```

## Coding Conventions

- Type hints on all function signatures
- Pydantic v2 for all request/response validation
- SQLAlchemy 2.0 style (mapped_column, DeclarativeBase)
- FastAPI dependency injection for DB sessions
- Keep modules small and focused
- Minimum complexity for the current task — no over-engineering

## Security Requirements

- **File uploads:** Validate file types (PDF, DOCX only), enforce size limits, sanitize filenames, store uploads outside web root
- **SQL injection:** Use SQLAlchemy ORM exclusively — no raw SQL string interpolation
- **API key handling:** Anthropic API key via environment variable only, never logged or exposed in responses
- **Input validation:** Pydantic models on all endpoints, reject unexpected fields
- **Path traversal:** Validate all file paths, never construct paths from user input without sanitization
- **CORS:** Configure explicitly for known origins only
- **Error responses:** Never leak stack traces, internal paths, or DB schema to clients

## Dependencies

**Core** (`[project.dependencies]`) — everything the app needs to run:
- fastapi, uvicorn, sqlalchemy, pydantic, pydantic-settings
- anthropic, python-docx, pymupdf (or pdfplumber)
- streamlit, requests

**Dev** (`[project.optional-dependencies]`) — testing/linting only:
- pytest, pytest-asyncio, httpx, ruff

Rule: if the Docker container would crash without it, it's a core dependency.

## Key Commands

```bash
# Run API
uvicorn ot_app.main:app --reload --port 8000

# Run frontend
streamlit run ot_frontend/app.py --server.port 8501

# Run both (via startup script)
./start.sh

# Tests
pytest

# Docker
docker compose up
```

## Open-Source Standards

- MIT License: `Copyright (c) 2026 Noam Raz and Pleasant Secret Labs`
- All sample data must be synthetic — never real company data
- `.gitignore` excludes: `.env`, `data/real/`, `data/*.db`, `__pycache__/`
- README leads with non-technical users: hosted URL > startup script > Docker > developer docs
