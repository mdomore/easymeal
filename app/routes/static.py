from fastapi import APIRouter, HTTPException, Depends, Request, Query
from fastapi.responses import FileResponse, Response, StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional

from app.storage import get_photo_object
from app.database import get_db, Meal
from app.auth import get_current_user, _get_token_from_request

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
    Serve photo directly from Supabase Storage.
    Requires authentication and verifies photo ownership.
    Supports authentication via Authorization header or token query parameter (for images).
    """
    # Get token from header or query parameter (for image requests that can't send headers)
    auth_token = _get_token_from_request(request) or token
    
    if not auth_token:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Verify token and get user
    # Create a request-like object with the token for authentication
    class TokenRequest:
        def __init__(self, token, original_request):
            self.headers = {"Authorization": f"Bearer {token}"}
            self.cookies = {}
            self.client = original_request.client
            self.url = original_request.url
    
    token_request = TokenRequest(auth_token, request)
    
    try:
        current_user_dict = await get_current_user(token_request, None, db)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid authentication")
    
    # Security: Verify that the photo belongs to a meal owned by the current user
    # First check photo_filename field (most common case)
    meal_by_filename = db.query(Meal).filter(
        Meal.photo_filename == filename,
        Meal.user_id == current_user_dict["id"]
    ).first()
    
    if meal_by_filename:
        # Photo found via photo_filename - access granted
        pass
    else:
        # Check photos JSON array for all user's meals
        # Note: JSON queries are database-specific, so we check in Python for portability
        meals = db.query(Meal).filter(Meal.user_id == current_user_dict["id"]).all()
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
            raise HTTPException(status_code=403, detail="Access denied: Photo not owned by user")
    
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
