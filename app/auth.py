from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
from sqlalchemy.orm import Session
import jwt

from app.database import get_db, User
from app.config import (
    SUPABASE_URL,
    SUPABASE_SERVICE_ROLE_KEY,
    SUPABASE_ANON_KEY,
    SUPABASE_JWT_SECRET
)
from app.security_logging import log_authentication_failure

# Create Supabase client with service role key for admin operations
# Initialize lazily to avoid startup errors
supabase: Optional[Client] = None

def get_supabase_client() -> Client:
    """Get or create Supabase client"""
    global supabase
    if supabase is None:
        if not SUPABASE_SERVICE_ROLE_KEY:
            raise ValueError("SUPABASE_SERVICE_ROLE_KEY not set")
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    return supabase

security = HTTPBearer(auto_error=False)


def _get_token_from_request(request: Request) -> Optional[str]:
    # Prefer Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        return auth_header.split(" ", 1)[1]
    # Fallback to cookie (Supabase uses sb-<project-ref>-auth-token)
    cookie_token = request.cookies.get("sb-access-token")
    if cookie_token:
        return cookie_token
    return None


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
):
    """
    Verify Supabase JWT token and return easymeal user information.
    Links Supabase Auth user to easymeal.users table via email.
    """
    token = _get_token_from_request(request)
    
    if not token:
        log_authentication_failure(request, reason="No token provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        # Verify JWT token using Supabase JWT secret
        decoded = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
            options={"verify_signature": True}
        )
        
        supabase_user_id = decoded.get("sub")
        email = decoded.get("email")
        
        if not supabase_user_id:
            log_authentication_failure(request, reason="Invalid token: missing user ID")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Find or create easymeal user linked to Supabase Auth user
        # First try to find by email
        easymeal_user = None
        if email:
            easymeal_user = db.query(User).filter(User.email == email).first()
        
        # If no user found by email, try to get username from token metadata and create user
        if not easymeal_user:
            # Get username from token metadata (stored during registration)
            username = decoded.get("user_metadata", {}).get("username") if decoded.get("user_metadata") else None
            
            # Create new easymeal user linked to Supabase Auth
            easymeal_user = User(
                username=username,
                email=email,
                password_hash=None,  # Password managed by Supabase
                is_temporary=False,
                is_premium=False
            )
            db.add(easymeal_user)
            db.commit()
            db.refresh(easymeal_user)
        
        return {
            "id": easymeal_user.id,
            "username": easymeal_user.username,
            "email": easymeal_user.email,
            "is_temporary": easymeal_user.is_temporary,
            "is_premium": easymeal_user.is_premium
        }
    except jwt.ExpiredSignatureError:
        log_authentication_failure(request, reason="Token expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        log_authentication_failure(request, reason="Invalid token format")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        log_authentication_failure(request, reason="Authentication error")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

