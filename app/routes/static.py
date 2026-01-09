from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, Response, StreamingResponse

from app.storage import get_photo_object

# Use a specific prefix to avoid conflicts with StaticFiles mount
router = APIRouter(prefix="/static/photos", tags=["static"])

# Note: Static files are served via app.mount("/static", ...) in main.py
# This router only handles photos from Supabase Storage at /static/photos/{filename}
# Regular static files are served by StaticFiles mount


@router.get("/{filename}")
async def serve_photo(filename: str):
    """Serve photo directly from Supabase Storage"""
    try:
        # Get photo from Supabase Storage
        photo_data = get_photo_object(filename)
        
        # Determine content type from filename
        content_type = "image/jpeg"
        if filename.lower().endswith('.png'):
            content_type = "image/png"
        elif filename.lower().endswith('.gif'):
            content_type = "image/gif"
        elif filename.lower().endswith('.webp'):
            content_type = "image/webp"
        
        # Reset stream position
        photo_data.seek(0)
        
        return StreamingResponse(
            photo_data,
            media_type=content_type,
            headers={
                "Cache-Control": "public, max-age=3600"
            }
        )
    except Exception as e:
        print(f"Error serving photo: {e}")
        raise HTTPException(status_code=404, detail="Photo not found")


# Note: sw.js and manifest.json are served by StaticFiles mount
# StaticFiles automatically sets correct MIME types
# If special headers are needed for service worker, we can add a route here
# For now, StaticFiles handles them correctly
