from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from app.config import DATABASE_URL

# SQLite: ensure DB directory exists and check_same_thread=False
_is_sqlite = (DATABASE_URL or "").strip().lower().startswith("sqlite")
if _is_sqlite:
    from pathlib import Path
    _path = DATABASE_URL.split("sqlite:///", 1)[-1].split("?")[0]
    if _path and _path != ":memory:":
        Path(_path).parent.mkdir(parents=True, exist_ok=True)
connect_args = {"check_same_thread": False} if _is_sqlite else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class Meal(Base):
    __tablename__ = "meals"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    url = Column(String, nullable=True)
    photo_filename = Column(String, nullable=True)
    photos = Column(JSON, nullable=True)  # [{"filename": "...", "is_primary": true}, ...]
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


def init_db():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
