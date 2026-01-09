"""
Cookie security middleware for FastAPI.
Ensures all cookies set by the application have secure settings:
- HttpOnly: Prevents JavaScript access (prevents XSS attacks)
- Secure: Only sent over HTTPS (in production)
- SameSite: Prevents CSRF attacks
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from typing import Callable
from app.config import ENVIRONMENT


class SecureCookieMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce secure cookie settings on all Set-Cookie headers.
    
    This ensures that any cookies set by the application (or downstream middleware)
    have secure attributes:
    - HttpOnly: Prevents JavaScript access
    - Secure: Only sent over HTTPS (in production)
    - SameSite=Lax: Prevents CSRF while allowing normal navigation
    """
    
    def __init__(self, app, environment: str = "development"):
        super().__init__(app)
        self.is_production = environment == "production"
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Process Set-Cookie headers to ensure secure settings
        if "Set-Cookie" in response.headers:
            cookies = response.headers.get_list("Set-Cookie")
            response.headers.pop("Set-Cookie", None)
            
            for cookie in cookies:
                # Parse cookie string (format: name=value; attr1=val1; attr2=val2)
                cookie_parts = cookie.split(";")
                if not cookie_parts:
                    continue
                
                # First part is name=value
                name_value = cookie_parts[0].strip()
                if not name_value:
                    continue
                
                # Parse attributes
                attrs = {}
                for part in cookie_parts[1:]:
                    part = part.strip()
                    if "=" in part:
                        key, value = part.split("=", 1)
                        attrs[key.strip().lower()] = value.strip()
                    else:
                        attrs[part.lower()] = True
                
                # Build secure cookie string
                secure_cookie = name_value
                
                # Add HttpOnly if not present (prevents JavaScript access)
                if "httponly" not in attrs:
                    secure_cookie += "; HttpOnly"
                
                # Add Secure flag in production (only send over HTTPS)
                if self.is_production and "secure" not in attrs:
                    secure_cookie += "; Secure"
                
                # Add SameSite if not present (prevents CSRF)
                if "samesite" not in attrs:
                    # Use Lax for most cookies (allows GET requests from other sites)
                    # Use Strict for sensitive cookies (no cross-site requests)
                    secure_cookie += "; SameSite=Lax"
                
                # Preserve other attributes (Path, Domain, Max-Age, Expires, etc.)
                for key, value in attrs.items():
                    if key not in ("httponly", "secure", "samesite"):
                        if value is True:
                            secure_cookie += f"; {key.capitalize()}"
                        else:
                            secure_cookie += f"; {key.capitalize()}={value}"
                
                response.headers.append("Set-Cookie", secure_cookie)
        
        return response
