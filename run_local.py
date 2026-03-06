"""
Entry point for local Docker: mount the app at /easymeal so the frontend URLs work unchanged.
Run with: uvicorn run_local:app --host 0.0.0.0 --port 8000
Then open http://localhost:8010/easymeal/
"""
from fastapi import FastAPI
from app.main import app as easymeal_app
from app.config import DISABLE_AUTH
from app.database import init_db

app = FastAPI(title="EasyMeal Local")
app.mount("/easymeal", easymeal_app)


@app.on_event("startup")
async def ensure_tables():
    """Mounted app's startup does not run; create tables when DISABLE_AUTH (e.g. SQLite)."""
    if DISABLE_AUTH:
        try:
            init_db()
            print("Database tables created (DISABLE_AUTH)")
        except Exception as e:
            print(f"Warning: init_db: {e}")
