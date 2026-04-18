import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# In Docker the /data volume is mounted; locally the file lands next to run.py.
_db_path = os.environ.get("DATABASE_PATH", "./tracktheticket.db")
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
