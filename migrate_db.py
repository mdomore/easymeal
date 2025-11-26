#!/usr/bin/env python3
"""
Migration script to transfer data from SQLite to PostgreSQL
and photos from filesystem to MinIO
"""
import sqlite3
import os
import sys
from pathlib import Path
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import Base, User, Meal, SessionLocal, engine
from app.storage import migrate_photos_from_filesystem, ensure_bucket_exists

# Configuration
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "data/meals.db")
PHOTOS_DIR = Path(os.getenv("PHOTOS_DIR", "data/photos"))


def migrate_users(session, sqlite_conn):
    """Migrate users from SQLite to PostgreSQL"""
    cursor = sqlite_conn.cursor()
    cursor.execute("SELECT id, username, email, password_hash, created_at FROM users")
    users = cursor.fetchall()
    
    migrated_count = 0
    for user_data in users:
        user_id, username, email, password_hash, created_at = user_data
        
        # Check if user already exists
        existing_user = session.query(User).filter(User.id == user_id).first()
        if existing_user:
            print(f"User {user_id} already exists, skipping...")
            continue
        
        # Parse created_at
        try:
            if isinstance(created_at, str):
                created_at_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            else:
                created_at_dt = datetime.utcnow()
        except:
            created_at_dt = datetime.utcnow()
        
        user = User(
            id=user_id,
            username=username,
            email=email,
            password_hash=password_hash,
            created_at=created_at_dt,
            is_temporary=False,
            is_premium=False
        )
        
        session.add(user)
        migrated_count += 1
        print(f"Migrated user: {username} (ID: {user_id})")
    
    session.commit()
    print(f"Migrated {migrated_count} users")
    return migrated_count


def migrate_meals(session, sqlite_conn):
    """Migrate meals from SQLite to PostgreSQL"""
    cursor = sqlite_conn.cursor()
    cursor.execute("""
        SELECT id, name, description, url, photo_filename, created_at, user_id 
        FROM meals
    """)
    meals = cursor.fetchall()
    
    migrated_count = 0
    for meal_data in meals:
        meal_id, name, description, url, photo_filename, created_at, user_id = meal_data
        
        # Check if meal already exists
        existing_meal = session.query(Meal).filter(Meal.id == meal_id).first()
        if existing_meal:
            print(f"Meal {meal_id} already exists, skipping...")
            continue
        
        # Parse created_at
        try:
            if isinstance(created_at, str):
                created_at_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            else:
                created_at_dt = datetime.utcnow()
        except:
            created_at_dt = datetime.utcnow()
        
        meal = Meal(
            id=meal_id,
            name=name,
            description=description,
            url=url,
            photo_filename=photo_filename,
            created_at=created_at_dt,
            user_id=user_id
        )
        
        session.add(meal)
        migrated_count += 1
        print(f"Migrated meal: {name} (ID: {meal_id})")
    
    session.commit()
    print(f"Migrated {migrated_count} meals")
    return migrated_count


def main():
    """Main migration function"""
    print("Starting database migration from SQLite to PostgreSQL...")
    
    # Check if SQLite database exists
    if not os.path.exists(SQLITE_DB_PATH):
        print(f"SQLite database not found at {SQLITE_DB_PATH}")
        print("Skipping migration - will initialize empty PostgreSQL database")
        Base.metadata.create_all(bind=engine)
        ensure_bucket_exists()
        return
    
    # Connect to SQLite
    print(f"Connecting to SQLite database: {SQLITE_DB_PATH}")
    sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
    
    # Initialize PostgreSQL database
    print("Initializing PostgreSQL database schema...")
    Base.metadata.create_all(bind=engine)
    
    # Create session
    session = SessionLocal()
    
    try:
        # Migrate users
        print("\n=== Migrating Users ===")
        user_count = migrate_users(session, sqlite_conn)
        
        # Migrate meals
        print("\n=== Migrating Meals ===")
        meal_count = migrate_meals(session, sqlite_conn)
        
        # Migrate photos
        print("\n=== Migrating Photos ===")
        if PHOTOS_DIR.exists():
            migrate_photos_from_filesystem(PHOTOS_DIR)
        else:
            print(f"Photos directory {PHOTOS_DIR} does not exist, skipping photo migration")
        
        print(f"\n=== Migration Complete ===")
        print(f"Users migrated: {user_count}")
        print(f"Meals migrated: {meal_count}")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
        raise
    finally:
        session.close()
        sqlite_conn.close()


if __name__ == "__main__":
    main()

