from fastapi import APIRouter, HTTPException, Depends, Request, Query
from fastapi.responses import FileResponse, Response, StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional

from app.storage import get_photo_object
from app.database import get_db, Meal
from app.auth import get_current_user, _get_token_from_request
from app.config import DISABLE_AUTH

# Use a specific prefix to avoid conflicts with StaticFiles mount
router = APIRouter(prefix="/static/photos", tags=["static"])

# Note: Static files are served via app.mount("/static", ...) in main.py
# This router only handles photos from Supabase Storage at /static/photos/{filename}
# Regular static files are served by StaticFiles mount


@router.get("/{filename}")
async def serve_photo(
    filename: str,
    request: Request,
    token: Optional[str] = Query(None, description="JWT token for authentication (for image requests)"),
    db: Session = Depends(get_db)
):
    """
    Serve photo from storage. Verifies photo belongs to a meal.
    When DISABLE_AUTH, no token required. Otherwise requires auth.
    """
    if not DISABLE_AUTH:
        auth_token = _get_token_from_request(request) or token
        if not auth_token:
            raise HTTPException(status_code=401, detail="Authentication required")
        class TokenRequest:
            def __init__(self, tok, original_request):
                self.headers = {"Authorization": f"Bearer {tok}"}
                self.cookies = {}
                self.client = original_request.client
                self.url = original_request.url
        try:
            await get_current_user(TokenRequest(auth_token, request), None)
        except HTTPException as e:
            raise e
        except Exception as e:
            print(f"Error authenticating photo request: {e}")
            raise HTTPException(status_code=401, detail="Invalid authentication")

    # Verify that the photo belongs to a meal
    meal_by_filename = db.query(Meal).filter(Meal.photo_filename == filename).first()
    if not meal_by_filename:
        meals = db.query(Meal).all()
        photo_found = False
        for meal in meals:
            if meal.photos and isinstance(meal.photos, list):
                for photo in meal.photos:
                    if isinstance(photo, dict) and photo.get("filename") == filename:
                        photo_found = True
                        break
            if photo_found:
                break
        if not photo_found:
            raise HTTPException(status_code=403, detail="Access denied: Photo not found")
    
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
