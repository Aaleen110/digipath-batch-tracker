from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    pass


# SQLite needs check_same_thread=False when FastAPI serves concurrent requests
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


# One session per request — FastAPI closes it after the handler returns
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()