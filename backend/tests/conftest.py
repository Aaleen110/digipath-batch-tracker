import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


# SQLite normally creates a separate in-memory database connection
# for each connection. StaticPool forces all test sessions to use
# the same connection so the database remains available throughout
# a test.
TEST_DATABASE_URL = "sqlite://"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture
def db_session():
    """
    Create a clean database for each test.

    Each test starts with an empty database and therefore cannot
    accidentally depend on data created by another test.
    """
    Base.metadata.create_all(bind=test_engine)

    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client(db_session):
    """
    Create a FastAPI test client using the isolated test database.
    """

    def override_get_db():
        yield db_session

    # Replace the application's real database dependency with our
    # isolated test database. This prevents tests from touching
    # batches.db.
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    # Always clear dependency overrides after the test so one test
    # cannot affect another test.
    app.dependency_overrides.clear()
