"""
File validation utilities for secure file uploads.
Validates file magic bytes (file signatures) to prevent file type spoofing.
"""
from typing import Tuple, Optional
import imghdr


# Magic bytes (file signatures) for common image formats
# Format: (signature_bytes, offset, mime_type, extension)
IMAGE_SIGNATURES = [
    # JPEG
    (b'\xff\xd8\xff', 0, 'image/jpeg', '.jpg'),
    # PNG
    (b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a', 0, 'image/png', '.png'),
    # GIF
    (b'\x47\x49\x46\x38\x37\x61', 0, 'image/gif', '.gif'),  # GIF87a
    (b'\x47\x49\x46\x38\x39\x61', 0, 'image/gif', '.gif'),  # GIF89a
    # WebP
    (b'RIFF', 0, 'image/webp', '.webp'),
    # BMP
    (b'BM', 0, 'image/bmp', '.bmp'),
    # TIFF
    (b'\x49\x49\x2a\x00', 0, 'image/tiff', '.tiff'),  # Little-endian
    (b'\x4d\x4d\x00\x2a', 0, 'image/tiff', '.tiff'),  # Big-endian
]

# Allowed image MIME types
ALLOWED_MIME_TYPES = {
    'image/jpeg',
    'image/jpg',
    'image/png',
    'image/gif',
    'image/webp',
    'image/bmp',
    'image/tiff',
    'image/tif'
}

# Allowed file extensions
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff', '.tif'}


def validate_image_magic_bytes(file_content: bytes) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Validate image file by checking magic bytes (file signature).
    
    Args:
        file_content: File content as bytes
    
    Returns:
        Tuple of (is_valid, mime_type, extension)
        Returns (False, None, None) if file is not a valid image
    """
    if not file_content or len(file_content) < 12:
        return False, None, None
    
    # Check against known image signatures
    for signature, offset, mime_type, extension in IMAGE_SIGNATURES:
        if len(file_content) > offset + len(signature):
            if file_content[offset:offset + len(signature)] == signature:
                # Special handling for WebP (RIFF...WEBP)
                if signature == b'RIFF':
                    if b'WEBP' in file_content[8:12]:
                        return True, mime_type, extension
                else:
                    return True, mime_type, extension
    
    # Fallback: Try using imghdr (Python's built-in image type detection)
    try:
        image_type = imghdr.what(None, h=file_content)
        if image_type:
            mime_type_map = {
                'jpeg': 'image/jpeg',
                'png': 'image/png',
                'gif': 'image/gif',
                'bmp': 'image/bmp',
                'tiff': 'image/tiff',
                'webp': 'image/webp'
            }
            ext_map = {
                'jpeg': '.jpg',
                'png': '.png',
                'gif': '.gif',
                'bmp': '.bmp',
                'tiff': '.tiff',
                'webp': '.webp'
            }
            mime = mime_type_map.get(image_type)
            ext = ext_map.get(image_type)
            if mime and ext:
                return True, mime, ext
    except Exception:
        pass
    
    return False, None, None


def validate_image_file(
    file_content: bytes,
    content_type: Optional[str] = None,
    filename: Optional[str] = None
) -> Tuple[bool, str, str]:
    """
    Comprehensive image file validation.
    Validates magic bytes, MIME type, and extension.
    
    Args:
        file_content: File content as bytes
        content_type: Reported MIME type from upload
        filename: Original filename
    
    Returns:
        Tuple of (is_valid, mime_type, extension)
    
    Raises:
        ValueError: If file is not a valid image
    """
    # Validate magic bytes first (most important - can't be spoofed)
    is_valid, detected_mime, detected_ext = validate_image_magic_bytes(file_content)
    
    if not is_valid:
        raise ValueError("File is not a valid image. Magic bytes do not match any known image format.")
    
    # Validate content type if provided
    if content_type:
        # Normalize content type
        content_type = content_type.lower().split(';')[0].strip()
        if content_type not in ALLOWED_MIME_TYPES:
            raise ValueError(f"Content type '{content_type}' is not allowed. Only image files are accepted.")
        
        # Check if content type matches detected type
        if detected_mime and content_type != detected_mime:
            # Allow some flexibility (e.g., image/jpg vs image/jpeg)
            if not (content_type in ['image/jpg', 'image/jpeg'] and detected_mime in ['image/jpeg', 'image/jpg']):
                raise ValueError(
                    f"Content type mismatch. Reported: {content_type}, "
                    f"detected: {detected_mime}. File may be spoofed."
                )
    
    # Validate extension if provided
    if filename:
        from pathlib import Path
        file_ext = Path(filename).suffix.lower()
        if file_ext and file_ext not in ALLOWED_EXTENSIONS:
            raise ValueError(f"File extension '{file_ext}' is not allowed. Only image files are accepted.")
        
        # Check if extension matches detected type
        if detected_ext and file_ext != detected_ext:
            # Allow some flexibility (e.g., .jpg vs .jpeg, .tif vs .tiff)
            jpeg_exts = {'.jpg', '.jpeg'}
            tiff_exts = {'.tiff', '.tif'}
            if not ((file_ext in jpeg_exts and detected_ext in jpeg_exts) or
                   (file_ext in tiff_exts and detected_ext in tiff_exts)):
                raise ValueError(
                    f"File extension mismatch. Reported: {file_ext}, "
                    f"detected: {detected_ext}. File may be spoofed."
                )
    
    return True, detected_mime, detected_ext


def get_safe_image_extension(file_content: bytes, fallback: str = '.jpg') -> str:
    """
    Get safe file extension based on actual file content (magic bytes).
    
    Args:
        file_content: File content as bytes
        fallback: Fallback extension if detection fails
    
    Returns:
        Safe file extension
    """
    _, _, extension = validate_image_magic_bytes(file_content)
    if extension:
        return extension
    return fallback
