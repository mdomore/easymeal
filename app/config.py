"""
Configuration management with environment variable validation.
Ensures all required secrets are provided and no insecure defaults are used.
"""
import os
from typing import Optional


def get_required_env(key: str, description: str = None) -> str:
    """
    Get a required environment variable. Raises ValueError if not set.
    
    Args:
        key: Environment variable name
        description: Optional description for error message
    
    Returns:
        Environment variable value
    
    Raises:
        ValueError: If environment variable is not set or is empty
    """
    value = os.getenv(key)
    if not value or value.strip() == "":
        desc = description or key
        raise ValueError(
            f"Required environment variable '{key}' is not set. "
            f"{desc} must be provided via environment variable."
        )
    return value


def get_optional_env(key: str, default: str = None, description: str = None) -> Optional[str]:
    """
    Get an optional environment variable with a default value.
    Only use for non-sensitive configuration values.
    
    Args:
        key: Environment variable name
        default: Default value if not set (only for non-sensitive config)
        description: Optional description
    
    Returns:
        Environment variable value or default
    """
    value = os.getenv(key, default)
    return value if value else None


# Database configuration
DATABASE_URL = get_required_env(
    "DATABASE_URL",
    "Database connection URL (e.g., postgresql://user:pass@host:port/dbname)"
)

# Supabase configuration
SUPABASE_URL = get_required_env(
    "SUPABASE_URL",
    "Supabase API URL"
)

SUPABASE_SERVICE_ROLE_KEY = get_required_env(
    "SUPABASE_SERVICE_ROLE_KEY",
    "Supabase service role key (required for admin operations)"
)

SUPABASE_ANON_KEY = get_optional_env(
    "SUPABASE_ANON_KEY",
    description="Supabase anonymous key (optional)"
)

# JWT secret - try SUPABASE_JWT_SECRET first, then JWT_SECRET, then use service role key as fallback
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET") or os.getenv("JWT_SECRET")
if not SUPABASE_JWT_SECRET:
    # If neither is set, use service role key (but warn if service role key is also not set)
    SUPABASE_JWT_SECRET = SUPABASE_SERVICE_ROLE_KEY
    if not SUPABASE_JWT_SECRET:
        raise ValueError(
            "SUPABASE_JWT_SECRET or JWT_SECRET must be set. "
            "Alternatively, SUPABASE_SERVICE_ROLE_KEY can be used as fallback."
        )

# Storage configuration
SUPABASE_BUCKET = get_optional_env(
    "SUPABASE_BUCKET",
    default="photos",
    description="Supabase Storage bucket name"
)

# Application configuration
ENVIRONMENT = get_optional_env(
    "ENVIRONMENT",
    default="development",
    description="Application environment (development/production)"
)

# CORS configuration
# Default allowed origins for local development and production
CORS_ORIGINS_LIST = [
    "http://localhost:8000",
    "http://localhost:3000",
    "https://micmoe.ddns.net",
    "http://micmoe.ddns.net",
]

# Add additional origins from environment variable (comma-separated)
ADDITIONAL_CORS_ORIGINS = get_optional_env(
    "CORS_ORIGINS",
    description="Additional CORS origins (comma-separated)"
)
if ADDITIONAL_CORS_ORIGINS:
    CORS_ORIGINS_LIST.extend([origin.strip() for origin in ADDITIONAL_CORS_ORIGINS.split(",")])