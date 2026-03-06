#!/usr/bin/env python3
"""
One-time migration: export meals (no user_id), drop user-related tables and
meals.user_id, recreate meals table, reimport meals.
Run with: python scripts/migrate_remove_users.py
Uses data/easymeal.db by default (or DATABASE_URL for SQLite).
"""
import json
import os
import sqlite3
import sys

# Default path for local Docker setup
DEFAULT_DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "easymeal.db")
EXPORT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "meals_export.json")


def get_db_path():
    url = os.getenv("DATABASE_URL", "")
    if url and url.strip().lower().startswith("sqlite"):
        path = url.split("sqlite:///", 1)[-1].split("?")[0]
        if path and path != ":memory:":
            return path
    return DEFAULT_DB


def export_meals(conn):
    cur = conn.execute(
        "SELECT id, name, description, url, photo_filename, photos, created_at FROM meals"
    )
    rows = cur.fetchall()
    columns = [d[0] for d in cur.description]
    meals = []
    for row in rows:
        d = dict(zip(columns, row))
        # photos is stored as JSON string in SQLite
        if isinstance(d.get("photos"), str):
            try:
                d["photos"] = json.loads(d["photos"]) if d["photos"] else None
            except json.JSONDecodeError:
                d["photos"] = None
        meals.append(d)
    return meals


def main():
    db_path = get_db_path()
    if not os.path.isfile(db_path):
        print(f"DB not found: {db_path}. Nothing to migrate.")
        return 0

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # 1) Export meals
    try:
        meals = export_meals(conn)
    except sqlite3.OperationalError as e:
        print(f"Export failed (table may not exist): {e}")
        conn.close()
        return 1
    with open(EXPORT_PATH, "w") as f:
        json.dump(meals, f, indent=2, default=str)
    print(f"Exported {len(meals)} meals to {EXPORT_PATH}")

    # 2) Drop tables (order due to FK)
    for table in ("referrals", "subscriptions", "meals", "users"):
        try:
            conn.execute(f"DROP TABLE IF EXISTS {table}")
        except sqlite3.OperationalError:
            pass
    conn.commit()
    print("Dropped old tables.")

    # 3) Create meals without user_id
    conn.execute("""
        CREATE TABLE meals (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            name VARCHAR NOT NULL,
            description TEXT,
            url VARCHAR,
            photo_filename VARCHAR,
            photos JSON,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
        )
    """)
    conn.commit()
    print("Created meals table (no user_id).")

    # 4) Reimport
    with open(EXPORT_PATH) as f:
        meals = json.load(f)
    for m in meals:
        photos = m.get("photos")
        if photos is not None and not isinstance(photos, str):
            photos = json.dumps(photos)
        conn.execute(
            """INSERT INTO meals (id, name, description, url, photo_filename, photos, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                m["id"],
                m["name"],
                m.get("description"),
                m.get("url"),
                m.get("photo_filename"),
                photos,
                m.get("created_at", ""),
            ),
        )
    # Reset SQLite sequence so next AUTOINCREMENT is after max id
    conn.execute("DELETE FROM sqlite_sequence WHERE name='meals'")
    if meals:
        conn.execute("INSERT INTO sqlite_sequence (name, seq) SELECT 'meals', MAX(id) FROM meals")
    conn.commit()
    print(f"Reimported {len(meals)} meals.")

    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
