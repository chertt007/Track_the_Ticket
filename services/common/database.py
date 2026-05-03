import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# All persistent .db files live in <project_root>/data/.
# Resolve the path absolutely so it works regardless of the process cwd.
_DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "tracktheticket.db"
_db_path = os.environ.get("DATABASE_PATH", str(_DEFAULT_DB_PATH))
DATABASE_URL = f"sqlite:///{_db_path}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # required for SQLite + FastAPI
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency — yields a DB session and closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
