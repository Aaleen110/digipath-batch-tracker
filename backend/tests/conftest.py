import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


# Tests use an isolated in-memory SQLite database instead of the
# development batches.db file.
#
# StaticPool keeps the same in-memory database available across
# different SQLAlchemy sessions. The sessions themselves are still
# created independently for each request.
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

    This fixture is useful for tests that need direct access to the
    database. API requests use the client fixture below and receive
    their own session.
    """
    Base.metadata.create_all(bind=test_engine)

    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client():
    """
    Create a FastAPI test client.

    A new SQLAlchemy session is created for every API request.
    This is important because concurrent requests must not share
    the same SQLAlchemy Session.
    """

    # Make sure the test database schema exists before requests begin.
    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        # Each API request gets its own independent SQLAlchemy session.
        #
        # This mirrors the application's real request lifecycle and
        # allows concurrent requests to operate independently.
        db = TestingSessionLocal()

        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    # Clear dependency overrides so one test cannot affect another.
    app.dependency_overrides.clear()

    # Remove all test data after the test completes.
    Base.metadata.drop_all(bind=test_engine)
