from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from typing import List
from sqlalchemy.orm import Session
from pathlib import Path
from io import BytesIO
import easyocr
from PIL import Image
import numpy as np

from app.database import get_db, Meal
from app.auth import get_current_user
from app.storage import upload_photo, delete_photo, get_photo_url
from app import schemas
from app.error_handler import create_safe_http_exception

router = APIRouter(prefix="/api/meals", tags=["meals"])


# Maximum file size: 10MB
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes

# Initialize EasyOCR reader (load models once at startup)
ocr_reader = None

def get_ocr_reader():
    """Get or initialize EasyOCR reader"""
    global ocr_reader
    if ocr_reader is None:
        print("Initializing EasyOCR reader (this may take a moment on first use)...")
        # Initialize with English and French support (can add more languages)
        ocr_reader = easyocr.Reader(['en', 'fr'], gpu=False)
        print("EasyOCR reader initialized")
    return ocr_reader


@router.get("/", response_model=List[schemas.MealResponse])
@router.get("", response_model=List[schemas.MealResponse])  # Also handle without trailing slash
async def get_meals(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all meals for the current user"""
    meals = db.query(Meal).filter(
        Meal.user_id == current_user["id"]
    ).order_by(Meal.created_at.desc()).all()
    
    return meals


@router.get("/{meal_id}", response_model=schemas.MealResponse)
async def get_meal(
    meal_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific meal by ID"""
    meal = db.query(Meal).filter(
        Meal.id == meal_id,
        Meal.user_id == current_user["id"]
    ).first()
    
    if meal is None:
        raise HTTPException(status_code=404, detail="Meal not found")
    
    return meal


@router.post("/", response_model=schemas.MealResponse, status_code=201)
@router.post("", response_model=schemas.MealResponse, status_code=201)  # Also handle without trailing slash
async def create_meal(
    meal: schemas.MealCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new meal"""
    new_meal = Meal(
        name=meal.name,
        description=meal.description,
        url=meal.url,
        photo_filename=meal.photo_filename,
        user_id=current_user["id"]
    )
    
    db.add(new_meal)
    db.commit()
    db.refresh(new_meal)
    
    return new_meal


@router.put("/{meal_id}", response_model=schemas.MealResponse)
async def update_meal(
    meal_id: int,
    meal: schemas.MealUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a meal"""
    db_meal = db.query(Meal).filter(
        Meal.id == meal_id,
        Meal.user_id == current_user["id"]
    ).first()
    
    if db_meal is None:
        raise HTTPException(status_code=404, detail="Meal not found")
    
    old_photo_filename = db_meal.photo_filename
    
    # Handle photo removal (empty string means remove)
    if meal.photo_filename == "" and old_photo_filename:
        delete_photo(old_photo_filename)
        db_meal.photo_filename = None
    
    # Update fields
    if meal.name is not None:
        db_meal.name = meal.name
    if meal.description is not None:
        db_meal.description = meal.description
    if meal.url is not None:
        db_meal.url = meal.url
    if meal.photo_filename is not None and meal.photo_filename != old_photo_filename:
        db_meal.photo_filename = meal.photo_filename
    
    db.commit()
    db.refresh(db_meal)
    
    return db_meal


@router.post("/upload-photo")
async def upload_photo_endpoint(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload a photo for a meal"""
    # Validate file type
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Check file size
    file_content = await file.read()
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413, 
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024 * 1024)}MB"
        )
    
    # Determine file extension
    file_ext = Path(file.filename).suffix if file.filename else '.jpg'
    if not file_ext:
        file_ext = '.jpg'
    
    # Upload to Supabase Storage
    try:
        filename = upload_photo(file_content, file_ext)
        return {"filename": filename}
    except Exception as e:
        raise create_safe_http_exception(
            status_code=500,
            generic_message="Failed to upload photo. Please try again.",
            error=e
        )


@router.post("/extract-text-from-photo")
async def extract_text_from_photo(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Extract text from a photo using OCR and upload the photo"""
    # Validate file type
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Check file size
    file_content = await file.read()
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413, 
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024 * 1024)}MB"
        )
    
    try:
        # Get OCR reader
        reader = get_ocr_reader()
        
        # Read image with EasyOCR
        # EasyOCR works with numpy arrays, so we'll use PIL to convert
        image = Image.open(BytesIO(file_content))
        image_array = np.array(image)
        
        # Extract text using EasyOCR
        results = reader.readtext(image_array)
        
        # Combine all detected text
        extracted_text = "\n".join([result[1] for result in results])
        
        # Clean up the text (remove extra whitespace)
        extracted_text = extracted_text.strip()
        
        # Upload photo to Supabase Storage
        file_ext = Path(file.filename).suffix if file.filename else '.jpg'
        if not file_ext:
            file_ext = '.jpg'
        filename = upload_photo(file_content, file_ext)
        
        return {
            "filename": filename,
            "extracted_text": extracted_text
        }
    except Exception as e:
        raise create_safe_http_exception(
            status_code=500,
            generic_message="Failed to process photo. Please try again.",
            error=e
        )


@router.delete("/{meal_id}", status_code=204)
async def delete_meal(
    meal_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a meal by ID"""
    meal = db.query(Meal).filter(
        Meal.id == meal_id,
        Meal.user_id == current_user["id"]
    ).first()
    
    if meal is None:
        raise HTTPException(status_code=404, detail="Meal not found")
    
    # Delete photo if exists
    if meal.photo_filename:
        delete_photo(meal.photo_filename)
    
    db.delete(meal)
    db.commit()
    
    return None


@router.get("/{meal_id}/photo")
async def get_meal_photo(
    meal_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get meal photo URL"""
    from fastapi.responses import RedirectResponse
    
    meal = db.query(Meal).filter(
        Meal.id == meal_id,
        Meal.user_id == current_user["id"]
    ).first()
    
    if not meal or not meal.photo_filename:
        raise HTTPException(status_code=404, detail="Photo not found")
    
    try:
        photo_url = get_photo_url(meal.photo_filename, expires_in_seconds=3600)
        return RedirectResponse(url=photo_url)
    except Exception as e:
        raise HTTPException(status_code=404, detail="Photo not found")
