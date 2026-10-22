import os
import sys
from pathlib import Path

# Keep test output readable and never call a real LLM.
os.environ["DEBUG"] = "false"
os.environ["LLM_ENABLED"] = "false"

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import get_db
from app.main import app
from app.models import Base, User
from app.seeds.seeder import seed_categories


@pytest.fixture()
def db():
    """Isolated in-memory database seeded like a fresh install."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSession()
    session.add(User(id=1, username="default"))
    session.commit()
    seed_categories(session)
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def client(db):
    """TestClient wired to the isolated session (no lifespan / scheduler)."""

    def _override_get_db():
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    test_client = TestClient(app)
    try:
        yield test_client
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.fixture()
def lenient_client(db):
    """Client that returns 500 responses instead of re-raising server errors."""

    def _override_get_db():
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    test_client = TestClient(app, raise_server_exceptions=False)
    try:
        yield test_client
    finally:
        app.dependency_overrides.pop(get_db, None)
