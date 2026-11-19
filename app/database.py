from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from app.config import DATABASE_URL

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=True)  # Nullable for temp accounts
    email = Column(String, unique=True, index=True, nullable=True)  # Nullable for temp accounts
    password_hash = Column(String, nullable=True)  # Nullable for temp accounts
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_temporary = Column(Boolean, default=False, nullable=False)
    is_premium = Column(Boolean, default=False, nullable=False)
    premium_until = Column(DateTime, nullable=True)
    referral_code = Column(String, unique=True, index=True, nullable=True)

    # Relationships
    meals = relationship("Meal", back_populates="user", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")
    referrals_sent = relationship("Referral", foreign_keys="Referral.referrer_id", back_populates="referrer")
    referrals_received = relationship("Referral", foreign_keys="Referral.referred_id", back_populates="referred")


class Meal(Base):
    __tablename__ = "meals"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    url = Column(String, nullable=True)
    photo_filename = Column(String, nullable=True)
    photos = Column(JSON, nullable=True)  # Array of photo objects: [{"filename": "...", "is_primary": true}, ...]
    tags = Column(JSON, nullable=True)  # ["Plat", "Végétarien", ...]
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    user = relationship("User", back_populates="meals")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    plan = Column(String, nullable=False)  # 'monthly', 'yearly', 'lifetime'
    status = Column(String, nullable=False)  # 'active', 'cancelled', 'expired'
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    payment_id = Column(String, nullable=True)  # Stripe/PayPal transaction ID

    # Relationships
    user = relationship("User", back_populates="subscriptions")


class Referral(Base):
    __tablename__ = "referrals"

    id = Column(Integer, primary_key=True, index=True)
    referrer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    referred_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String, nullable=False, default="pending")  # 'pending', 'completed', 'rewarded'
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    reward_given_at = Column(DateTime, nullable=True)

    # Relationships
    referrer = relationship("User", foreign_keys=[referrer_id], back_populates="referrals_sent")
    referred = relationship("User", foreign_keys=[referred_id], back_populates="referrals_received")


def _ensure_meal_columns():
    """Add missing columns on existing tables (create_all does not alter)."""
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

