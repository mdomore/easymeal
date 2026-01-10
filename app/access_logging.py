"""
Access logging middleware to log all HTTP requests.
"""
import logging
import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.security_logging import get_client_info

# Create a dedicated logger for access logs
access_logger = logging.getLogger("access")
access_logger.setLevel(logging.INFO)
# Ensure logs propagate and are displayed
access_logger.propagate = False

# Create a handler if one doesn't exist
if not access_logger.handlers:
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        '%(asctime)s - %(message)s'
    )
    handler.setFormatter(formatter)
    access_logger.addHandler(handler)


class AccessLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all HTTP requests with client info and response status."""
    
    async def dispatch(self, request: Request, call_next):
        # Record start time for response time calculation
        start_time = time.time()
        
        # Get client information
        client_info = get_client_info(request)
        client_ip = client_info["ip"]
        method = client_info["method"]
        path = client_info["path"]
        user_agent = client_info.get("user_agent", "unknown")
        
        # Process request
        response = await call_next(request)
        
        # Calculate response time
        process_time = time.time() - start_time
        
        # Get status code
        status_code = response.status_code
        
        # Log the access (similar to Apache/Nginx combined log format)
        # Format: IP - - [timestamp] "METHOD PATH HTTP/1.1" STATUS_CODE SIZE "REFERER" "USER_AGENT" PROCESS_TIME
        referer = client_info.get("referer", "-")
        
        log_message = (
            f'{client_ip} - - "{method} {path} HTTP/1.1" {status_code} - '
            f'"{referer}" "{user_agent}" {process_time:.4f}s'
        )
        
        # Use both logger and print to ensure logs appear
        access_logger.info(log_message)
        print(log_message, flush=True)  # flush=True ensures immediate output
        
        return response
