import os
import logging
from typing import Optional

# Configure logging
logger = logging.getLogger(__name__)

# Check if we're in production mode
IS_PRODUCTION = os.getenv("ENVIRONMENT", "development").lower() in ("production", "prod")


def get_safe_error_message(
    error: Exception,
    generic_message: str,
    log_details: bool = True
) -> str:
    """
    Get a safe error message that doesn't leak internal details in production.
    
    Args:
        error: The exception that occurred
        generic_message: Generic message to show to users
        log_details: Whether to log detailed error information server-side
    
    Returns:
        Safe error message for client (generic in production, detailed in development)
    """
    error_details = str(error)
    error_type = type(error).__name__
    
    # Always log detailed error server-side for debugging
    if log_details:
        logger.error(f"Error occurred: {error_type}: {error_details}", exc_info=True)
    
    # In production, return generic message
    if IS_PRODUCTION:
        return generic_message
    
    # In development, return more detailed message (but still sanitized)
    # Don't expose full stack traces or sensitive paths
    safe_details = error_details
    # Remove potential sensitive information
    if "password" in safe_details.lower():
        safe_details = "Error contains sensitive information"
    elif "token" in safe_details.lower() and "secret" in safe_details.lower():
        safe_details = "Authentication error"
    
    return f"{generic_message} ({error_type})"


def create_safe_http_exception(
    status_code: int,
    generic_message: str,
    error: Optional[Exception] = None,
    log_details: bool = True
):
    """
    Create an HTTPException with safe error message.
    
    Args:
        status_code: HTTP status code
        generic_message: Generic message for users
        error: Optional exception that occurred
        log_details: Whether to log detailed error
    
    Returns:
        HTTPException with safe error message
    """
    from fastapi import HTTPException
    
    if error:
        detail = get_safe_error_message(error, generic_message, log_details)
    else:
        detail = generic_message
    
    return HTTPException(status_code=status_code, detail=detail)
