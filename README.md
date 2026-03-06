# Contract Obligation Tracker & Compliance Dashboard

Extract and track contract obligations, deadlines, SLAs, and deliverables. Upload contracts (PDF/DOCX), get AI-powered obligation extraction, and monitor compliance through a visual dashboard with calendar views, health scores, and filterable tables.

## Getting Started

### Option 1: Hosted Version
> Coming soon — a hosted version will be available at a public URL.

### Option 2: Run Locally (Recommended)

```bash
./start.sh        # macOS / Linux
start.bat         # Windows
```

This automatically sets up Python, installs dependencies, starts the API and dashboard, and opens your browser. No configuration needed to explore with sample data.

### Option 3: Docker

```bash
docker compose up
```

Then open http://localhost:8501.

### Optional: Enable AI Extraction

To extract obligations from your own contracts using AI, set your Anthropic API key:

```bash
# Create a .env file
echo "ANTHROPIC_API_KEY=your-key-here" > .env
```

Without an API key, you can still:
- Load and explore sample data (8 synthetic contracts, ~45 obligations)
- Manually add contracts and obligations
- Use all dashboard and calendar features

## Features

- **Upload contracts** — PDF and Word (.docx) formats, up to 50 MB
- **AI-powered extraction** — Automatically identifies obligations, deadlines, SLAs, penalties, and responsible parties
- **Dashboard** — Portfolio summary with health scores, status breakdowns, and risk analysis
- **Calendar view** — Visual month/week/day view of upcoming obligations, color-coded by risk
- **Filterable tables** — Filter by contract, type, status, risk level, responsible party, and date range
- **Health scores** — Per-contract compliance score based on completion rate, overdue penalties, and risk exposure
- **Status tracking** — 6 statuses (Pending, In Progress, Completed, Overdue, Waived, Escalated) with full audit trail
- **Manual entry** — Add contracts and obligations manually; records indicate AI vs. manual source
- **Sample data** — 8 synthetic contracts with ~45 pre-built obligations for immediate exploration

## Deploy Your Own

### Railway (One-Click Cloud Deploy)

1. Fork this repo
2. Connect to [Railway](https://railway.app)
3. Set environment variables: `ANTHROPIC_API_KEY` (optional)
4. Deploy — Railway uses `Dockerfile.railway` automatically

## For Developers

### API Documentation

With the API running, visit http://localhost:8000/docs for interactive Swagger documentation.

### Project Structure

```
obligation-tracker/
├── ot_app/                  # FastAPI backend
│   ├── main.py              # App entry point
│   ├── config.py            # Settings (pydantic-settings)
│   ├── database.py          # SQLAlchemy engine and session
│   ├── models/              # ORM models (Contract, Obligation, StatusHistory)
│   ├── schemas/             # Pydantic request/response schemas
│   ├── routers/             # API route modules
│   ├── services/            # Business logic (extraction, scoring, demo)
│   └── utils/               # Document parsing, section detection, file handling
├── ot_frontend/             # Streamlit dashboard
│   ├── app.py               # Main entry point
│   ├── api_client.py        # HTTP client for API
│   └── pages/               # Dashboard, Contracts, Obligations, Calendar, Settings
├── tests/                   # pytest test suite
├── data/sample/             # Synthetic sample contracts and obligations
├── pyproject.toml           # Dependencies and project config
├── start.sh / start.bat     # One-command launch scripts
├── Dockerfile               # API container
├── docker-compose.yml       # Multi-service orchestration
└── Dockerfile.railway       # Single-container cloud deploy
```

### Tech Stack

- **Backend:** Python 3.11+, FastAPI, SQLAlchemy 2.0, Pydantic v2
- **AI:** Anthropic API (Claude) for obligation extraction
- **Document parsing:** python-docx, PyMuPDF
- **Database:** SQLite (prototype), designed for PostgreSQL migration
- **Frontend:** Streamlit with streamlit-calendar
- **Deployment:** Docker, Railway

### Running Tests

```bash
pip install -e ".[dev]"
pytest
```

### Key API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/contracts` | List contracts |
| POST | `/api/v1/contracts/upload` | Upload contract file |
| POST | `/api/v1/contracts/{id}/extract` | AI extraction |
| GET | `/api/v1/obligations` | List/filter obligations |
| PATCH | `/api/v1/obligations/{id}/status` | Change status |
| GET | `/api/v1/obligations/calendar` | Calendar events |
| GET | `/api/v1/dashboard/summary` | Portfolio stats |
| POST | `/api/v1/demo/load` | Load sample data |

## License

MIT License — Copyright (c) 2026 Noam Raz and Pleasant Secret Labs
