from fastapi import APIRouter, HTTPException, Depends, Request, Query
from fastapi.responses import StreamingResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import cast, String
from typing import Optional

from app.storage import get_photo_object, get_browser_photo_url
from app.database import get_db, Meal
from app.auth import get_current_user, _get_token_from_request
from app.config import DISABLE_AUTH

router = APIRouter(prefix="/static/photos", tags=["static"])


def _meal_owns_photo(db: Session, filename: str) -> bool:
    """Fast ownership check without loading every meal into Python."""
    if db.query(Meal.id).filter(Meal.photo_filename == filename).first():
        return True
    # photos JSON array: match filename substring (UUID filenames → safe enough)
    return (
        db.query(Meal.id)
        .filter(Meal.photos.isnot(None), cast(Meal.photos, String).like(f"%{filename}%"))
        .first()
        is not None
    )


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
    Redirects to public Supabase URL when available; otherwise streams bytes.
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

    if not _meal_owns_photo(db, filename):
        raise HTTPException(status_code=403, detail="Access denied: Photo not found")

    # Prefer redirect to public storage (avoids proxying large images through the API)
    public_url = get_browser_photo_url(filename)
    if public_url:
        return RedirectResponse(
            url=public_url,
            status_code=302,
            headers={"Cache-Control": "public, max-age=86400"},
        )

    try:
        photo_data = get_photo_object(filename)

        content_type = "image/jpeg"
        lower = filename.lower()
        if lower.endswith('.png'):
            content_type = "image/png"
        elif lower.endswith('.gif'):
            content_type = "image/gif"
        elif lower.endswith('.webp'):
            content_type = "image/webp"

        photo_data.seek(0)

        return StreamingResponse(
            photo_data,
            media_type=content_type,
            headers={
                "Cache-Control": "public, max-age=86400"
            }
        )
    except Exception as e:
        print(f"Error serving photo: {e}")
        raise HTTPException(status_code=404, detail="Photo not found")
