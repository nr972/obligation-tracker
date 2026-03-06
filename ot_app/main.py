"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ot_app import __version__
from ot_app.config import settings
from ot_app.database import Base, SessionLocal, engine
from ot_app.routers import contracts, dashboard, obligations, system
from ot_app.services.obligation_service import check_and_update_overdue


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables and check for overdue obligations
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        check_and_update_overdue(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="Contract Obligation Tracker",
    description="Extract and track contract obligations, deadlines, and compliance.",
    version=__version__,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(contracts.router, prefix="/api/v1")
app.include_router(obligations.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(system.router, prefix="/api/v1")
