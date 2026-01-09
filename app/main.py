from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from app.database import init_db
from app.storage import ensure_bucket_exists
from app.routes import auth, meals, static
from app.config import CORS_ORIGINS
from alembic.config import Config
from alembic import command

app = FastAPI(title="EasyMeal Recipe App", version="1.0.0", root_path="/easymeal")

# CORS middleware for frontend integration
# Restrict to specific origins for security
allowed_origins = [
    "http://localhost:8000",
    "http://localhost:3000",
    "https://micmoe.ddns.net",
    "http://micmoe.ddns.net",
]

# Allow additional origins from environment variable (comma-separated)
if CORS_ORIGINS:
    allowed_origins.extend([origin.strip() for origin in CORS_ORIGINS.split(",")])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(meals.router)
app.include_router(static.router)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.on_event("startup")
async def startup_event():
    """Run database migrations and initialize Supabase Storage bucket on startup"""
    # Run Alembic migrations
    try:
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        print("Database migrations completed successfully")
    except Exception as e:
        print(f"Warning: Could not run migrations: {e}")
        print("Falling back to init_db()")
        # Fallback to init_db if migrations fail (for backward compatibility)
        try:
            init_db()
        except Exception as init_error:
            print(f"Warning: Could not initialize database: {init_error}")
    
    # Initialize Supabase Storage bucket
    try:
        ensure_bucket_exists()
    except Exception as e:
        print(f"Warning: Could not initialize Supabase Storage bucket: {e}")
    # Note: OCR reader will be initialized lazily on first use to avoid slow startup
