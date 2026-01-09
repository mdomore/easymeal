from fastapi import Request, HTTPException, status, Depends
from collections import defaultdict
import time
from app.security_logging import log_rate_limit_exceeded


# Rate limit storage: {ip: [(timestamp, endpoint), ...]}
_rate_limit_store: dict[str, list[tuple[float, str]]] = defaultdict(list)

# Rate limit configuration
RATE_LIMIT_WINDOW = 60  # 1 minute window
RATE_LIMIT_MAX_REQUESTS = 5  # Max 5 requests per window per IP


def get_client_ip(request: Request) -> str:
    """Extract client IP address from request"""
    # Check for forwarded IP (when behind proxy/load balancer)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For can contain multiple IPs, take the first one
        return forwarded_for.split(",")[0].strip()
    
    # Check for real IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    
    # Fallback to direct client IP
    if request.client:
        return request.client.host
    
    return "unknown"


def cleanup_old_entries(ip: str, current_time: float):
    """Remove entries older than the rate limit window"""
    if ip in _rate_limit_store:
        cutoff_time = current_time - RATE_LIMIT_WINDOW
        _rate_limit_store[ip] = [
            (timestamp, endpoint)
            for timestamp, endpoint in _rate_limit_store[ip]
            if timestamp > cutoff_time
        ]


def check_rate_limit(ip: str, endpoint: str) -> bool:
    """Check if request is within rate limit. Returns True if allowed, False if rate limited."""
    current_time = time.time()
    
    # Clean up old entries for this IP
    cleanup_old_entries(ip, current_time)
    
    # Count requests in current window for this endpoint
    endpoint_requests = [
        timestamp for timestamp, ep in _rate_limit_store[ip]
        if ep == endpoint and timestamp > current_time - RATE_LIMIT_WINDOW
    ]
    
    if len(endpoint_requests) >= RATE_LIMIT_MAX_REQUESTS:
        return False
    
    # Add current request
    _rate_limit_store[ip].append((current_time, endpoint))
    return True


def rate_limit_dependency(endpoint_name: str):
    """
    FastAPI dependency for rate limiting.
    
    Args:
        endpoint_name: Name of the endpoint being rate limited
    """
    async def check_rate_limit_dep(request: Request):
        client_ip = get_client_ip(request)
        
        if not check_rate_limit(client_ip, endpoint_name):
            # Log rate limit violation
            log_rate_limit_exceeded(request, endpoint_name)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many requests. Please try again in {RATE_LIMIT_WINDOW} seconds.",
                headers={"Retry-After": str(RATE_LIMIT_WINDOW)}
            )
        return True
    
    return check_rate_limit_dep
