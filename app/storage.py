from pathlib import Path
import uuid
from io import BytesIO
import requests

from app.config import (
    SUPABASE_URL,
    SUPABASE_SERVICE_ROLE_KEY,
    SUPABASE_ANON_KEY,
    SUPABASE_BUCKET,
    DISABLE_AUTH,
    LOCAL_PHOTOS_PATH,
)

# Use service role key, fallback to anon key if service role not available
SUPABASE_KEY = (SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY) if not DISABLE_AUTH else None

# Local photos directory for DISABLE_AUTH mode
_local_photos_dir: Path = None


def _get_local_photos_dir() -> Path:
    global _local_photos_dir
    if _local_photos_dir is None:
        _local_photos_dir = Path(LOCAL_PHOTOS_PATH or "data/photos")
        _local_photos_dir.mkdir(parents=True, exist_ok=True)
    return _local_photos_dir


def get_headers():
    """Get common headers for Supabase API requests"""
    return {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "apikey": SUPABASE_KEY
    }


def ensure_bucket_exists():
    """Create bucket if it doesn't exist (no-op when using local storage)."""
    if DISABLE_AUTH:
        return
    try:
        # Check if bucket exists
        response = requests.get(
            f"{SUPABASE_URL}/storage/v1/bucket",
            headers=get_headers()
        )
        
        if response.status_code == 200:
            buckets = response.json()
            bucket_names = [b.get("name") for b in buckets] if isinstance(buckets, list) else []
            
            if SUPABASE_BUCKET not in bucket_names:
                # Create bucket with public access
                create_response = requests.post(
                    f"{SUPABASE_URL}/storage/v1/bucket",
                    headers=get_headers(),
                    json={
                        "name": SUPABASE_BUCKET,
                        "public": True,
                        "file_size_limit": 52428800  # 50MB limit
                    }
                )
                if create_response.status_code in [200, 201]:
                    print(f"Created bucket: {SUPABASE_BUCKET}")
                else:
                    print(f"Warning: Could not create bucket: {create_response.text}")
    except Exception as e:
        print(f"Error ensuring bucket exists: {e}")
        # Don't raise - bucket might already exist


def optimize_image(image_data: bytes, max_width: int = 1920, max_height: int = 1920, quality: int = 85) -> bytes:
    """Optimize image by resizing and compressing"""
    try:
        from PIL import Image
        from io import BytesIO
        
        # Open image
        img = Image.open(BytesIO(image_data))
        
        # Convert RGBA to RGB if necessary (for JPEG)
        if img.mode in ('RGBA', 'LA', 'P'):
            # Create white background
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Calculate new dimensions while maintaining aspect ratio
        original_width, original_height = img.size
        ratio = min(max_width / original_width, max_height / original_height, 1.0)
        
        if ratio < 1.0:
            new_width = int(original_width * ratio)
            new_height = int(original_height * ratio)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Compress and save as JPEG
        output = BytesIO()
        img.save(output, format='JPEG', quality=quality, optimize=True)
        output.seek(0)
        
        return output.read()
    except Exception as e:
        print(f"Error optimizing image: {e}")
        # Return original if optimization fails
        return image_data


def upload_photo(file_content: bytes, file_extension: str = ".jpg") -> str:
    """Upload photo to Supabase Storage or local disk and return filename (with optimization)."""
    # Optimize image before uploading
    try:
        optimized_content = optimize_image(file_content)
        original_size = len(file_content)
        optimized_size = len(optimized_content)
        reduction = ((original_size - optimized_size) / original_size * 100) if original_size > 0 else 0
        print(f"Image optimized: {original_size / 1024:.1f}KB -> {optimized_size / 1024:.1f}KB ({reduction:.1f}% reduction)")
        file_content = optimized_content
        file_extension = ".jpg"  # Always save as JPEG after optimization
    except Exception as e:
        print(f"Warning: Image optimization failed, using original: {e}")
    
    filename = f"{uuid.uuid4()}{file_extension}"
    
    if DISABLE_AUTH:
        photos_dir = _get_local_photos_dir()
        path = photos_dir / filename
        path.write_bytes(file_content)
        return filename
    
    ensure_bucket_exists()
    try:
        content_type = "image/jpeg"
        headers = get_headers()
        headers["Content-Type"] = content_type
        headers["x-upsert"] = "false"
        response = requests.post(
            f"{SUPABASE_URL}/storage/v1/object/{SUPABASE_BUCKET}/{filename}",
            headers=headers,
            data=file_content
        )
        if response.status_code not in [200, 201]:
            raise Exception(f"Upload error: {response.status_code} - {response.text}")
        return filename
    except Exception as e:
        print(f"Error uploading photo: {e}")
        raise


def get_photo_object(filename: str):
    """Get photo object from Supabase Storage or local disk."""
    if DISABLE_AUTH:
        photos_dir = _get_local_photos_dir()
        path = photos_dir / filename
        if not path.is_file():
            raise FileNotFoundError(f"Photo not found: {filename}")
        return BytesIO(path.read_bytes())
    try:
        response = requests.get(
            f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{filename}",
            headers=get_headers()
        )
        if response.status_code == 200:
            return BytesIO(response.content)
        raise Exception(f"Download error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error getting photo: {e}")
        raise


def delete_photo(filename: str):
    """Delete photo from Supabase Storage or local disk."""
    if DISABLE_AUTH:
        photos_dir = _get_local_photos_dir()
        path = photos_dir / filename
        if path.is_file():
            path.unlink(missing_ok=True)
        return
    try:
        requests.delete(
            f"{SUPABASE_URL}/storage/v1/object/{SUPABASE_BUCKET}/{filename}",
            headers=get_headers()
        )
    except Exception as e:
        print(f"Error deleting photo: {e}")


def get_photo_url(filename: str, expires_in_seconds: int = 3600) -> str:
    """Get public URL for photo. When DISABLE_AUTH, returns app-relative path for router to serve."""
    if DISABLE_AUTH:
        # Served by app at /static/photos/{filename}?token=...
        return f"/static/photos/{filename}"
    try:
        base_url = SUPABASE_URL.rstrip('/')
        return f"{base_url}/storage/v1/object/public/{SUPABASE_BUCKET}/{filename}"
    except Exception as e:
        print(f"Error generating photo URL: {e}")
        raise


def migrate_photos_from_filesystem(photos_dir: Path):
    """Migrate photos from filesystem to Supabase Storage"""
    ensure_bucket_exists()
    
    if not photos_dir.exists():
        print(f"Photos directory {photos_dir} does not exist")
        return
    
    migrated_count = 0
    for photo_file in photos_dir.iterdir():
        if photo_file.is_file() and photo_file.suffix.lower() in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
            try:
                with open(photo_file, "rb") as f:
                    file_content = f.read()
                
                # Upload to Supabase Storage with same filename
                upload_photo(file_content, photo_file.suffix)
                
                migrated_count += 1
                print(f"Migrated photo: {photo_file.name}")
            except Exception as e:
                print(f"Error migrating photo {photo_file.name}: {e}")
    
    print(f"Migrated {migrated_count} photos to Supabase Storage")
