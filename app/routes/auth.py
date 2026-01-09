from fastapi import APIRouter, HTTPException, Depends, status, Request
from sqlalchemy.orm import Session
import jwt

from app.database import get_db, User
from app.auth import get_current_user, get_supabase_client
from app import schemas
from app.rate_limit import rate_limit_dependency
from app.config import SUPABASE_JWT_SECRET
from app.error_handler import create_safe_http_exception
from app.security_logging import (
    log_failed_login, log_successful_login,
    log_failed_registration, log_successful_registration,
    log_rate_limit_exceeded, log_authentication_failure
)

router = APIRouter(prefix="/api", tags=["auth"])


@router.post("/register", response_model=schemas.UserResponse, status_code=201)
async def register(
    user: schemas.UserRegister,
    request: Request,
    db: Session = Depends(get_db),
    _: bool = Depends(rate_limit_dependency("register"))
):
    """Register a new user with Supabase Auth"""
    try:
        # Check if username exists in easymeal
        existing_user = db.query(User).filter(User.username == user.username).first()
        if existing_user:
            log_failed_registration(request, user_identifier=user.username, reason="Username already registered")
            raise HTTPException(status_code=400, detail="Username already registered")
        
        # Register with Supabase Auth
        supabase = get_supabase_client()
        response = supabase.auth.sign_up({
            "email": user.email,
            "password": user.password,
            "options": {
                "data": {
                    "username": user.username
                }
            }
        })
        
        if response.user is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registration failed"
            )
        
        # Create easymeal user linked to Supabase Auth
        new_user = User(
            username=user.username,
            email=user.email,
            password_hash=None,  # Password managed by Supabase
            is_temporary=False,
            is_premium=False
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Log successful registration
        log_successful_registration(request, user_identifier=user.username)

        return {
            "id": new_user.id,
            "username": new_user.username,
            "email": new_user.email,
            "is_temporary": new_user.is_temporary,
            "is_premium": new_user.is_premium
        }
    except HTTPException as e:
        # Log failed registration
        if e.status_code == 400:
            log_failed_registration(request, user_identifier=user.username, reason=str(e.detail))
        raise
    except Exception as e:
        error_msg = str(e).lower()
        if "already registered" in error_msg or "already exists" in error_msg or "user already registered" in error_msg:
            log_failed_registration(request, user_identifier=user.username, reason="Email already registered")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        # Use safe error handler to prevent information leakage
        raise create_safe_http_exception(
            status_code=status.HTTP_400_BAD_REQUEST,
            generic_message="Registration failed. Please try again.",
            error=e
        )


@router.post("/login", response_model=schemas.Token)
async def login(
    user: schemas.UserLogin,
    request: Request,
    db: Session = Depends(get_db),
    _: bool = Depends(rate_limit_dependency("login"))
):
    """Login with Supabase Auth - supports both username and email. Auto-creates easymeal user if needed."""
    try:
        # Determine email: try username as email, or lookup from easymeal DB
        email = None
        
        # Check if username is actually an email
        if "@" in user.username:
            email = user.username
        else:
            # Try to find user by username in easymeal DB
            db_user = db.query(User).filter(User.username == user.username).first()
            if db_user and db_user.email:
                email = db_user.email
            else:
                # If not found, try username as email (for backward compatibility)
                email = user.username
        
        # Login with Supabase Auth
        supabase = get_supabase_client()
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": user.password,
        })
        
        if not response.session or not response.session.access_token:
            log_failed_login(request, user_identifier=user.username, reason="Invalid credentials")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Decode token to get user info and create/update easymeal user if needed
        try:
            decoded = jwt.decode(
                response.session.access_token,
                SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                options={"verify_signature": False}
            )
            supabase_email = decoded.get("email")
            supabase_metadata = decoded.get("user_metadata", {})
            username = supabase_metadata.get("username") or user.username
            
            # Create or update easymeal user if needed
            if supabase_email:
                easymeal_user = db.query(User).filter(User.email == supabase_email).first()
                if not easymeal_user:
                    # Create new easymeal user linked to Supabase Auth
                    easymeal_user = User(
                        username=username,
                        email=supabase_email,
                        password_hash=None,  # Password managed by Supabase
                        is_temporary=False,
                        is_premium=False
                    )
                    db.add(easymeal_user)
                    db.commit()
                    print(f"Created easymeal user for {supabase_email}")
        except Exception as user_creation_error:
            print(f"Warning: Could not create easymeal user: {user_creation_error}")
        
        # Log successful login
        log_successful_login(request, user_identifier=email)
        
        return {
            "access_token": response.session.access_token,
            "token_type": "bearer"
        }
    except HTTPException as e:
        # Log failed login
        if e.status_code == 401:
            log_failed_login(request, user_identifier=user.username, reason=str(e.detail))
        raise
    except Exception as e:
        # Log failed login
        log_failed_login(request, user_identifier=user.username, reason="Login error")
        # Use safe error handler - don't expose internal error details
        # Log server-side for debugging, but return generic message to client
        raise create_safe_http_exception(
            status_code=status.HTTP_401_UNAUTHORIZED,
            generic_message="Invalid credentials",
            error=e
        )


@router.get("/me", response_model=schemas.UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    return current_user
