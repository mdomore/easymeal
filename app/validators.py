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

# Allowed HTML tags for rich text descriptions (from Quill editor)
ALLOWED_HTML_TAGS = {'p', 'br', 'strong', 'b', 'em', 'i', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 
                     'ul', 'ol', 'li', 'a', 'blockquote', 'pre', 'code'}
ALLOWED_HTML_ATTRIBUTES = {'href', 'target', 'rel'}


def sanitize_html(text: str) -> str:
    """Escape HTML characters to prevent XSS attacks (for plain text fields)"""
    if not text:
        return text
    return html.escape(text)


def sanitize_rich_html(html_content: str) -> str:
    """
    Sanitize rich HTML content to allow safe tags while removing dangerous ones.
    Used for descriptions that come from Quill editor.
    """
    if not html_content:
        return html_content
    
    # Remove script tags and their content
    html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove event handlers (onclick, onerror, etc.)
    html_content = re.sub(r'\s*on\w+\s*=\s*["\'][^"\']*["\']', '', html_content, flags=re.IGNORECASE)
    
    # Remove javascript: and data: URLs
    html_content = re.sub(r'javascript:', '', html_content, flags=re.IGNORECASE)
    html_content = re.sub(r'data:text/html', '', html_content, flags=re.IGNORECASE)
    
    # Remove style tags and inline styles
    html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.IGNORECASE | re.DOTALL)
    html_content = re.sub(r'\s*style\s*=\s*["\'][^"\']*["\']', '', html_content, flags=re.IGNORECASE)
    
    # Remove dangerous tags but keep allowed ones
    # First, escape all tags
    # Then unescape allowed tags
    # This is a simple approach - for production, consider using a library like bleach
    
    # Remove tags that are not in the allowed list
    allowed_tags_pattern = '|'.join(ALLOWED_HTML_TAGS)
    # Keep allowed tags, remove others
    html_content = re.sub(
        r'</?(?!' + allowed_tags_pattern + r'\b)[^>]+>',
        '',
        html_content,
        flags=re.IGNORECASE
    )
    
    # Clean up attributes on allowed tags - only keep href, target, rel
    for tag in ALLOWED_HTML_TAGS:
        # Remove all attributes except allowed ones
        pattern = rf'<{tag}\s+([^>]*)>'
        def clean_attrs(match):
            attrs = match.group(1)
            # Extract only allowed attributes
            allowed_attrs = []
            for attr in ALLOWED_HTML_ATTRIBUTES:
                attr_pattern = rf'\b{attr}\s*=\s*["\']([^"\']*)["\']'
                attr_match = re.search(attr_pattern, attrs, re.IGNORECASE)
                if attr_match:
                    allowed_attrs.append(f'{attr}="{html.escape(attr_match.group(1))}"')
            if allowed_attrs:
                return f'<{tag} {" ".join(allowed_attrs)}>'
            return f'<{tag}>'
        
        html_content = re.sub(pattern, clean_attrs, html_content, flags=re.IGNORECASE)
    
    return html_content


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
    """Validate and sanitize description (allows safe HTML from Quill editor)"""
    if not description:
        return None
    
    description = description.strip()
    
    if len(description) > DESCRIPTION_MAX_LENGTH:
        raise ValueError(f"Description must be no more than {DESCRIPTION_MAX_LENGTH} characters long")
    
    # Sanitize HTML to allow safe tags but remove dangerous ones
    # This allows rich text from Quill editor while preventing XSS
    description = sanitize_rich_html(description)
    
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
