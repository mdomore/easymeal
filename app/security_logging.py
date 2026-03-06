"""
Security / request helpers. get_client_info used by access logging.
"""
from typing import Dict, Any
from fastapi import Request


def get_client_info(request: Request) -> Dict[str, Any]:
    """
    Extract client information from request for logging.
    Does not include sensitive data.
    """
    client_ip = request.client.host if request.client else "unknown"
    if "X-Forwarded-For" in request.headers:
        client_ip = request.headers["X-Forwarded-For"].split(",")[0].strip()
    elif "X-Real-IP" in request.headers:
        client_ip = request.headers["X-Real-IP"].strip()

    return {
        "ip": client_ip,
        "user_agent": request.headers.get("User-Agent", "unknown"),
        "method": request.method,
        "path": request.url.path,
        "referer": request.headers.get("Referer"),
    }
