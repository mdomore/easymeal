import re
from typing import Optional
from urllib.parse import urlparse
import html


# Validation constants
USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 30
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128
MEAL_NAME_MAX_LENGTH = 200
DESCRIPTION_MAX_LENGTH = 10000
URL_MAX_LENGTH = 2048

# Allowed username pattern: alphanumeric, underscore, hyphen, no spaces
USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')

# Allowed URL schemes
ALLOWED_URL_SCHEMES = {'http', 'https'}


def sanitize_html(text: str) -> str:
    """Escape HTML characters to prevent XSS attacks"""
    if not text:
        return text
    return html.escape(text)


def validate_username(username: str) -> str:
    """Validate and sanitize username"""
    if not username:
        raise ValueError("Username is required")
    
    username = username.strip()
    
    if len(username) < USERNAME_MIN_LENGTH:
        raise ValueError(f"Username must be at least {USERNAME_MIN_LENGTH} characters long")
    
    if len(username) > USERNAME_MAX_LENGTH:
        raise ValueError(f"Username must be no more than {USERNAME_MAX_LENGTH} characters long")
    
    if not USERNAME_PATTERN.match(username):
        raise ValueError("Username can only contain letters, numbers, underscores, and hyphens")
    
    return username


def validate_password(password: str) -> str:
    """Validate password length"""
    if not password:
        raise ValueError("Password is required")
    
    if len(password) < PASSWORD_MIN_LENGTH:
        raise ValueError(f"Password must be at least {PASSWORD_MIN_LENGTH} characters long")
    
    if len(password) > PASSWORD_MAX_LENGTH:
        raise ValueError(f"Password must be no more than {PASSWORD_MAX_LENGTH} characters long")
    
    return password


def validate_meal_name(name: str) -> str:
    """Validate and sanitize meal name"""
    if not name:
        raise ValueError("Meal name is required")
    
    name = name.strip()
    
    if len(name) > MEAL_NAME_MAX_LENGTH:
        raise ValueError(f"Meal name must be no more than {MEAL_NAME_MAX_LENGTH} characters long")
    
    # Sanitize HTML
    name = sanitize_html(name)
    
    return name


def validate_description(description: Optional[str]) -> Optional[str]:
    """Validate and sanitize description"""
    if not description:
        return None
    
    description = description.strip()
    
    if len(description) > DESCRIPTION_MAX_LENGTH:
        raise ValueError(f"Description must be no more than {DESCRIPTION_MAX_LENGTH} characters long")
    
    # Sanitize HTML to prevent XSS
    description = sanitize_html(description)
    
    return description


def validate_url(url: Optional[str]) -> Optional[str]:
    """Validate URL format and scheme"""
    if not url:
        return None
    
    url = url.strip()
    
    if len(url) > URL_MAX_LENGTH:
        raise ValueError(f"URL must be no more than {URL_MAX_LENGTH} characters long")
    
    # Parse URL to validate format
    try:
        parsed = urlparse(url)
        
        # Check if URL has a scheme
        if not parsed.scheme:
            # If no scheme, assume http and prepend it
            url = f"http://{url}"
            parsed = urlparse(url)
        
        # Validate scheme is allowed
        if parsed.scheme not in ALLOWED_URL_SCHEMES:
            raise ValueError(f"URL scheme must be one of: {', '.join(ALLOWED_URL_SCHEMES)}")
        
        # Validate URL has a netloc (domain)
        if not parsed.netloc:
            raise ValueError("Invalid URL format")
        
        return url
    except Exception as e:
        raise ValueError(f"Invalid URL format: {str(e)}")


def sanitize_filename(filename: Optional[str]) -> Optional[str]:
    """Sanitize filename to prevent path traversal and other attacks"""
    if not filename:
        return None
    
    # Remove any path components
    filename = filename.split('/')[-1].split('\\')[-1]
    
    # Remove any potentially dangerous characters
    filename = re.sub(r'[^a-zA-Z0-9._-]', '', filename)
    
    # Limit length
    if len(filename) > 255:
        filename = filename[:255]
    
    return filename
