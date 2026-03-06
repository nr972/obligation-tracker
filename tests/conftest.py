"""Shared test fixtures."""

import pytest
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

from ot_app.database import Base, get_db
from ot_app.models import Contract, Obligation, StatusHistory  # noqa: F401


@pytest.fixture
def db_engine():
    """Create an in-memory SQLite engine shared across threads."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture
def db_session(db_engine):
    """Create a DB session for testing."""
    TestSession = sessionmaker(bind=db_engine)
    session = TestSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    """Create a FastAPI test client with overridden DB dependency."""
    from fastapi.testclient import TestClient

    from ot_app.main import app

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
