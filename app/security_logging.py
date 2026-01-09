"""
Security event logging module.
Logs security-relevant events without exposing sensitive data.
"""
import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import Request

# Create a dedicated logger for security events
security_logger = logging.getLogger("security")
security_logger.setLevel(logging.WARNING)  # Only log warnings and above by default

# Create a handler if one doesn't exist
if not security_logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    security_logger.addHandler(handler)


def get_client_info(request: Request) -> Dict[str, Any]:
    """
    Extract client information from request for logging.
    Does not include sensitive data.
    """
    # Get client IP (considering proxies)
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


def log_security_event(
    event_type: str,
    request: Request,
    level: str = "WARNING",
    details: Optional[Dict[str, Any]] = None,
    user_identifier: Optional[str] = None
):
    """
    Log a security event with structured data.
    
    Args:
        event_type: Type of security event (e.g., "failed_login", "rate_limit_exceeded")
        request: FastAPI Request object
        level: Log level (INFO, WARNING, ERROR)
        details: Additional event details (must not contain sensitive data)
        user_identifier: Username or email (not password or token)
    """
    client_info = get_client_info(request)
    
    log_data = {
        "event_type": event_type,
        "timestamp": datetime.utcnow().isoformat(),
        "client": client_info,
        "user_identifier": user_identifier,  # Only username/email, never password
    }
    
    if details:
        # Sanitize details to ensure no sensitive data
        sanitized_details = {}
        for key, value in details.items():
            # Skip sensitive fields
            if key.lower() in ("password", "token", "secret", "key", "credential"):
                sanitized_details[key] = "[REDACTED]"
            else:
                sanitized_details[key] = value
        log_data["details"] = sanitized_details
    
    # Log as JSON for easier parsing
    message = json.dumps(log_data)
    
    if level == "ERROR":
        security_logger.error(message)
    elif level == "WARNING":
        security_logger.warning(message)
    else:
        security_logger.info(message)


def log_failed_login(request: Request, user_identifier: Optional[str] = None, reason: Optional[str] = None):
    """Log a failed login attempt"""
    details = {}
    if reason:
        details["reason"] = reason
    log_security_event(
        "failed_login",
        request,
        level="WARNING",
        details=details,
        user_identifier=user_identifier
    )


def log_successful_login(request: Request, user_identifier: str):
    """Log a successful login (INFO level)"""
    log_security_event(
        "successful_login",
        request,
        level="INFO",
        user_identifier=user_identifier
    )


def log_failed_registration(request: Request, user_identifier: Optional[str] = None, reason: Optional[str] = None):
    """Log a failed registration attempt"""
    details = {}
    if reason:
        details["reason"] = reason
    log_security_event(
        "failed_registration",
        request,
        level="WARNING",
        details=details,
        user_identifier=user_identifier
    )


def log_successful_registration(request: Request, user_identifier: str):
    """Log a successful registration"""
    log_security_event(
        "successful_registration",
        request,
        level="INFO",
        user_identifier=user_identifier
    )


def log_rate_limit_exceeded(request: Request, endpoint: str, user_identifier: Optional[str] = None):
    """Log when rate limit is exceeded"""
    log_security_event(
        "rate_limit_exceeded",
        request,
        level="WARNING",
        details={"endpoint": endpoint},
        user_identifier=user_identifier
    )


def log_authentication_failure(request: Request, reason: Optional[str] = None):
    """Log authentication failure (e.g., invalid token)"""
    details = {}
    if reason:
        details["reason"] = reason
    log_security_event(
        "authentication_failure",
        request,
        level="WARNING",
        details=details
    )


def log_authorization_failure(request: Request, user_identifier: Optional[str] = None, resource: Optional[str] = None):
    """Log authorization failure (e.g., access denied)"""
    details = {}
    if resource:
        details["resource"] = resource
    log_security_event(
        "authorization_failure",
        request,
        level="WARNING",
        details=details,
        user_identifier=user_identifier
    )


def log_suspicious_activity(request: Request, activity_type: str, details: Optional[Dict[str, Any]] = None):
    """Log suspicious activity that might indicate an attack"""
    log_security_event(
        "suspicious_activity",
        request,
        level="ERROR",
        details={**(details or {}), "activity_type": activity_type}
    )
