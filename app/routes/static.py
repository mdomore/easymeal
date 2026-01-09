from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, Response, StreamingResponse

from app.storage import get_photo_object

router = APIRouter(tags=["static"])


@router.get("/static/photos/{filename}")
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


@router.get("/static/sw.js")
async def serve_service_worker():
    """Serve service worker with correct content type"""
    with open("static/sw.js", "r") as f:
        content = f.read()
    return Response(
        content=content,
        media_type="application/javascript",
        headers={"Service-Worker-Allowed": "/easymeal/"}
    )


@router.get("/static/manifest.json")
async def serve_manifest():
    """Serve manifest.json with correct content type"""
    return FileResponse("static/manifest.json", media_type="application/manifest+json")


@router.get("/")
async def read_root():
    return FileResponse("static/index.html")
