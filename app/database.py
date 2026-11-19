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
    tags = Column(JSON, nullable=True)  # ["Plat", "Végétarien", ...]
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


def _ensure_meal_columns():
    """Add missing columns on existing SQLite/Postgres tables (create_all does not alter)."""
    from sqlalchemy import inspect, text
    try:
        inspector = inspect(engine)
        if "meals" not in inspector.get_table_names():
            return
        existing = {c["name"] for c in inspector.get_columns("meals")}
        if "tags" not in existing:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE meals ADD COLUMN tags JSON"))
            print("Added meals.tags column")
    except Exception as e:
        print(f"Warning: could not ensure meal columns: {e}")


def init_db():
    """Create all tables and ensure schema updates"""
    Base.metadata.create_all(bind=engine)
    _ensure_meal_columns()


def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
