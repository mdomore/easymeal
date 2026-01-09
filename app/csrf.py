"""
CSRF protection middleware and utilities for FastAPI.
Implements CSRF token validation for state-changing operations.
"""
import secrets
from typing import Optional
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import jwt
from app.config import SUPABASE_JWT_SECRET


# State-changing HTTP methods that require CSRF protection
CSRF_PROTECTED_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

# CSRF token header name
CSRF_TOKEN_HEADER = "X-CSRF-Token"


def generate_csrf_token() -> str:
    """Generate a secure random CSRF token"""
    return secrets.token_urlsafe(32)


def get_csrf_token_from_request(request: Request) -> Optional[str]:
    """Extract CSRF token from request header"""
    return request.headers.get(CSRF_TOKEN_HEADER)


def validate_csrf_token(request: Request, token: Optional[str]) -> bool:
    """
    Validate CSRF token for the request.
    For JWT-based auth, we validate that:
    1. Token is provided in header
    2. User is authenticated (valid JWT)
    
    Note: For a more secure implementation, we could:
    - Store CSRF tokens in a database/cache keyed by user_id
    - Embed CSRF token in JWT payload and validate it matches
    - Use a signed token that includes user_id and timestamp
    
    For now, we require a token header for authenticated requests,
    which provides basic CSRF protection since browsers won't automatically
    send custom headers in cross-origin requests.
    """
    if not token:
        return False
    
    # Extract JWT token to verify user is authenticated
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.lower().startswith("bearer "):
        return False
    
    jwt_token = auth_header.split(" ", 1)[1]
    
    try:
        # Decode JWT to verify it's valid
        decoded = jwt.decode(
            jwt_token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
            options={"verify_signature": True}
        )
        
        # Token is valid and user is authenticated
        # The presence of a custom header provides CSRF protection
        # since browsers don't automatically send custom headers in cross-origin requests
        return True
        
    except jwt.InvalidTokenError:
        return False


class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce CSRF protection on state-changing operations.
    
    Requires X-CSRF-Token header for POST, PUT, PATCH, DELETE requests
    that require authentication.
    
    Public endpoints like /api/register and /api/login are exempt
    since they don't require authentication and CSRF is less relevant.
    """
    
    # Public endpoints that don't require CSRF protection
    PUBLIC_ENDPOINTS = {"/api/register", "/api/login"}
    
    async def dispatch(self, request: Request, call_next):
        # Skip CSRF check for safe methods (GET, HEAD, OPTIONS)
        if request.method not in CSRF_PROTECTED_METHODS:
            return await call_next(request)
        
        # Skip CSRF check for public endpoints
        if request.url.path in self.PUBLIC_ENDPOINTS:
            return await call_next(request)
        
        # For authenticated endpoints, require CSRF token
        # Check if request has Authorization header (authenticated)
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.lower().startswith("bearer "):
            # This is an authenticated request - require CSRF token
            csrf_token = get_csrf_token_from_request(request)
            
            if not validate_csrf_token(request, csrf_token):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="CSRF token missing or invalid"
                )
        
        response = await call_next(request)
        return response


def get_csrf_token_dependency(request: Request):
    """
    Dependency to get CSRF token from request.
    Can be used in endpoints that need to return CSRF tokens.
    """
    token = get_csrf_token_from_request(request)
    if not token:
        # Generate new token if not provided
        token = generate_csrf_token()
    return token
