from minio import Minio
from minio.error import S3Error
import os
from pathlib import Path
import uuid
from urllib.parse import urlparse

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "photos")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"
# External URL for presigned URLs (accessible from browser)
MINIO_EXTERNAL_URL = os.getenv("MINIO_EXTERNAL_URL", None)

# Initialize MinIO client
minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=MINIO_SECURE
)


def ensure_bucket_exists():
    """Create bucket if it doesn't exist"""
    try:
        if not minio_client.bucket_exists(MINIO_BUCKET):
            minio_client.make_bucket(MINIO_BUCKET)
    except S3Error as e:
        print(f"Error ensuring bucket exists: {e}")
        raise


def upload_photo(file_content: bytes, file_extension: str = ".jpg") -> str:
    """Upload photo to MinIO and return filename"""
    ensure_bucket_exists()
    
    # Generate unique filename
    filename = f"{uuid.uuid4()}{file_extension}"
    
    try:
        from io import BytesIO
        file_stream = BytesIO(file_content)
        file_size = len(file_content)
        
        # Determine content type based on extension
        content_type_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp"
        }
        content_type = content_type_map.get(file_extension.lower(), "image/jpeg")
        
        minio_client.put_object(
            MINIO_BUCKET,
            filename,
            file_stream,
            file_size,
            content_type=content_type
        )
        
        return filename
    except S3Error as e:
        print(f"Error uploading photo: {e}")
        raise


def get_photo_object(filename: str):
    """Get photo object from MinIO"""
    try:
        from io import BytesIO
        response = minio_client.get_object(MINIO_BUCKET, filename)
        data = BytesIO(response.read())
        response.close()
        response.release_conn()
        return data
    except S3Error as e:
        print(f"Error getting photo: {e}")
        raise


def delete_photo(filename: str):
    """Delete photo from MinIO"""
    try:
        minio_client.remove_object(MINIO_BUCKET, filename)
    except S3Error as e:
        print(f"Error deleting photo: {e}")
        # Don't raise - photo might not exist


def get_photo_url(filename: str, expires_in_seconds: int = 3600) -> str:
    """Get presigned URL for photo (valid for expires_in_seconds)"""
    try:
        from datetime import timedelta
        url = minio_client.presigned_get_object(
            MINIO_BUCKET,
            filename,
            expires=timedelta(seconds=expires_in_seconds)
        )
        
        # Replace internal Docker hostname with external URL if configured
        if MINIO_EXTERNAL_URL:
            # Parse the presigned URL and replace the hostname
            parsed = urlparse(url)
            external_parsed = urlparse(MINIO_EXTERNAL_URL)
            # Reconstruct URL with external hostname but keep the path and query
            url = f"{external_parsed.scheme}://{external_parsed.netloc}{parsed.path}?{parsed.query}"
        elif "minio:9000" in url:
            # If no external URL configured but we see internal hostname, use localhost with http
            url = url.replace("http://minio:9000", "http://localhost:9000")
            url = url.replace("https://minio:9000", "http://localhost:9000")
            # Also handle if protocol is missing
            if url.startswith("minio:9000"):
                url = url.replace("minio:9000", "localhost:9000")
                if not url.startswith("http"):
                    url = f"http://{url}"
        
        # Ensure http (not https) for localhost since MinIO is not using SSL
        if "localhost:9000" in url and url.startswith("https://"):
            url = url.replace("https://", "http://")
        
        return url
    except S3Error as e:
        print(f"Error generating photo URL: {e}")
        raise


def migrate_photos_from_filesystem(photos_dir: Path):
    """Migrate photos from filesystem to MinIO"""
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
                
                # Upload to MinIO with same filename
                filename = photo_file.name
                from io import BytesIO
                file_stream = BytesIO(file_content)
                
                minio_client.put_object(
                    MINIO_BUCKET,
                    filename,
                    file_stream,
                    len(file_content),
                    content_type=f"image/{photo_file.suffix[1:].lower()}"
                )
                
                migrated_count += 1
                print(f"Migrated photo: {filename}")
            except Exception as e:
                print(f"Error migrating photo {photo_file.name}: {e}")
    
    print(f"Migrated {migrated_count} photos to MinIO")

