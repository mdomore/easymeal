from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from app.database import init_db
from app.storage import ensure_bucket_exists
from app.routes import meals, static
from app.config import CORS_ORIGINS_LIST, ENVIRONMENT, DISABLE_AUTH
from app.security_headers import SecurityHeadersMiddleware
from app.csrf import CSRFProtectionMiddleware
from app.cookie_security import SecureCookieMiddleware
from app.access_logging import AccessLoggingMiddleware
from alembic.config import Config
from alembic import command
from fastapi import Request, status
from fastapi.responses import JSONResponse

app = FastAPI(title="EasyMeal Recipe App", version="1.0.0", root_path="/easymeal")

# Access logging middleware (should be early to capture all requests)
app.add_middleware(AccessLoggingMiddleware)

# Security headers middleware (must be added first to apply to all responses)
app.add_middleware(
    SecurityHeadersMiddleware,
    environment=ENVIRONMENT
)

# Secure cookie middleware (ensures all cookies have secure settings)
app.add_middleware(
    SecureCookieMiddleware,
    environment=ENVIRONMENT
)

# CSRF protection middleware (after security headers, before CORS)
app.add_middleware(CSRFProtectionMiddleware)

# CORS middleware for frontend integration
# Restrict to specific origins for security
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS_LIST,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers (no auth router; app runs without users)
app.include_router(meals.router)
app.include_router(static.router)  # Has /static/photos/{filename} route

# Serve static files using explicit route to ensure correct MIME types
# This works around issues with StaticFiles mount and root_path
# Note: This route comes AFTER routers, so /static/photos/{filename} is handled by the router first
from fastapi.responses import FileResponse
import os

@app.get("/static/{file_path:path}")
async def serve_static_file(file_path: str):
    """Serve static files with correct MIME types (excludes /static/photos which is handled by router)"""
    # Skip photos path - handled by static router
    if file_path.startswith("photos/"):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="File not found")
    
    # Security: prevent path traversal
    file_path = os.path.normpath(file_path)
    if ".." in file_path or file_path.startswith("/"):
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Access denied")
    
    full_path = os.path.join("static", file_path)
    if not os.path.exists(full_path):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="File not found")
    
    # Determine MIME type from extension
    media_type = "application/octet-stream"
    if file_path.endswith(".css"):
        media_type = "text/css"
    elif file_path.endswith(".js"):
        # Service workers must be served with application/javascript or text/javascript
        media_type = "application/javascript"
    elif file_path.endswith(".html"):
        media_type = "text/html"
    elif file_path.endswith(".json"):
        media_type = "application/json"
    elif file_path.endswith(".png"):
        media_type = "image/png"
    elif file_path.endswith(".jpg") or file_path.endswith(".jpeg"):
        media_type = "image/jpeg"
    elif file_path.endswith(".gif"):
        media_type = "image/gif"
    elif file_path.endswith(".webp"):
        media_type = "image/webp"
    elif file_path.endswith(".svg"):
        media_type = "image/svg+xml"
    elif file_path.endswith(".ico"):
        media_type = "image/x-icon"
    elif file_path.endswith(".woff") or file_path.endswith(".woff2"):
        media_type = "font/woff" if file_path.endswith(".woff") else "font/woff2"
    
    # Allow the service worker at /easymeal/static/sw.js to control /easymeal/
    headers = {}
    if file_path == "sw.js":
        headers["Service-Worker-Allowed"] = "/easymeal/"
    
    return FileResponse(full_path, media_type=media_type, headers=headers)


@app.get("/")
async def read_root():
    """Serve the main index.html page"""
    from fastapi.responses import FileResponse
    return FileResponse("static/index.html")


# Global exception handler to ensure all errors return JSON
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions and return JSON responses"""
    from fastapi import HTTPException
    
    # If it's already an HTTPException, let FastAPI handle it
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )
    
    # Log the error
    import traceback
    traceback.print_exc()
    
    # Return a safe JSON error response
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please try again."}
    )


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
        try:
            init_db()
        except Exception as init_error:
            print(f"Warning: Could not initialize database: {init_error}")
    if DISABLE_AUTH:
        # Ensure tables exist (initial migration may be empty)
        try:
            init_db()
        except Exception as e:
            print(f"Warning: init_db (DISABLE_AUTH): {e}")
    
    # Initialize Supabase Storage bucket
    try:
        ensure_bucket_exists()
    except Exception as e:
        print(f"Warning: Could not initialize Supabase Storage bucket: {e}")
    # Note: OCR reader will be initialized lazily on first use to avoid slow startup
