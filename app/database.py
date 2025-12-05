from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://easymeal:easymeal@localhost:5432/easymeal")

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

