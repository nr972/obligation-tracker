# Package Naming Convention

This project is part of a portfolio where multiple projects may be installed
in the same Python environment. To prevent module collisions, use
project-specific package names instead of generic `app/` and `frontend/`.

## Required package names for this project

| Generic name | Use instead |
|---|---|
| `app/` | `ot_app/` |
| `frontend/` | `ot_frontend/` |

## Examples

- Backend entry point: `uvicorn ot_app.main:app`
- Frontend entry point: `streamlit run ot_frontend/app.py`
- Imports: `from ot_app.config import settings`
- pyproject.toml package discovery: `include = ["ot_app*", "ot_frontend*"]`

## Why

When multiple projects use `app/` as their package name and are installed
via `pip install -e .`, Python cannot distinguish between them. One project's
`app.config` shadows another's, causing silent import errors at runtime.
