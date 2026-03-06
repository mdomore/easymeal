from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import DISABLE_AUTH

security = HTTPBearer(auto_error=False)


def _get_token_from_request(request: Request) -> Optional[str]:
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        return auth_header.split(" ", 1)[1]
    cookie_token = request.cookies.get("sb-access-token")
    if cookie_token:
        return cookie_token
    return None


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
):
    """
    When DISABLE_AUTH is True, no login required; return a constant placeholder.
    When DISABLE_AUTH is False, authentication would require JWT (auth router not mounted in local setup).
    """
    if DISABLE_AUTH:
        return {"id": 1}
    token = _get_token_from_request(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Auth not configured (DISABLE_AUTH mode only)",
        headers={"WWW-Authenticate": "Bearer"},
    )
