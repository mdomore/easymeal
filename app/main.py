from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, FileResponse
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime, timedelta
import os
from jose import JWTError, jwt
import bcrypt
from pathlib import Path
from sqlalchemy.orm import Session
import uuid
from io import BytesIO
import pytesseract
from PIL import Image

from app.database import get_db, init_db, User, Meal
from app.storage import upload_photo, delete_photo, get_photo_url, get_photo_object, ensure_bucket_exists

app = FastAPI(title="EasyMeal Recipe App", version="1.0.0", root_path="/easymeal")

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60  # 30 days

security = HTTPBearer()

# Pydantic models
class UserResponse(BaseModel):
    id: Optional[int] = None
    username: Optional[str] = None
    email: Optional[str] = None
    is_temporary: Optional[bool] = None
    is_premium: Optional[bool] = None

    class Config:
        from_attributes = True


class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str


class AccountConvert(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class MealResponse(BaseModel):
    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    url: Optional[str] = None
    photo_filename: Optional[str] = None
    created_at: Optional[datetime] = None
    user_id: Optional[int] = None

    class Config:
        from_attributes = True


class MealCreate(BaseModel):
    name: str
    description: Optional[str] = None
    url: Optional[str] = None
    photo_filename: Optional[str] = None


class MealUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    photo_filename: Optional[str] = None


# Password hashing
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


# JWT functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# Helper function to create temporary account
def create_temporary_account(db: Session) -> User:
    """Create a new temporary account"""
    temp_user = User(
        username=None,
        email=None,
        password_hash=None,
        is_temporary=True,
        is_premium=False
    )
    db.add(temp_user)
    db.commit()
    db.refresh(temp_user)
    return temp_user


# Authentication dependency
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        if credentials is None:
            raise credentials_exception
            
        token = credentials.credentials
        
        if not token:
            raise credentials_exception
        
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except JWTError:
            raise credentials_exception
        
        user_id_str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        
        try:
            user_id = int(user_id_str)
        except (ValueError, TypeError):
            raise credentials_exception
        
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise credentials_exception
        
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_temporary": user.is_temporary,
            "is_premium": user.is_premium
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR: Auth error: {e}")
        raise credentials_exception


@app.on_event("startup")
async def startup_event():
    """Initialize database and MinIO bucket on startup"""
    init_db()
    try:
        ensure_bucket_exists()
    except Exception as e:
        print(f"Warning: Could not initialize MinIO bucket: {e}")


# Serve photos from MinIO directly
@app.get("/static/photos/{filename}")
async def serve_photo(filename: str):
    """Serve photo directly from MinIO"""
    try:
        from fastapi.responses import StreamingResponse
        from io import BytesIO
        
        # Get photo from MinIO
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


# Serve service worker with correct MIME type
@app.get("/static/sw.js")
async def serve_service_worker():
    """Serve service worker with correct content type"""
    from fastapi.responses import Response
    with open("static/sw.js", "r") as f:
        content = f.read()
    return Response(
        content=content,
        media_type="application/javascript",
        headers={"Service-Worker-Allowed": "/easymeal/"}
    )

# Serve manifest.json
@app.get("/static/manifest.json")
async def serve_manifest():
    """Serve manifest.json with correct content type"""
    return FileResponse("static/manifest.json", media_type="application/manifest+json")

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def read_root():
    return FileResponse("static/index.html")


# Authentication endpoints
@app.post("/api/register", response_model=UserResponse, status_code=201)
async def register(user: UserRegister, db: Session = Depends(get_db)):
    # Check if username exists
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Check if email exists
    existing_email = db.query(User).filter(User.email == user.email).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    password_hash = get_password_hash(user.password)
    new_user = User(
        username=user.username,
        email=user.email,
        password_hash=password_hash,
        is_temporary=False,
        is_premium=False
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {
        "id": new_user.id,
        "username": new_user.username,
        "email": new_user.email,
        "is_temporary": new_user.is_temporary,
        "is_premium": new_user.is_premium
    }


@app.post("/api/login", response_model=Token)
async def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Temporary accounts cannot login with username/password
    if db_user.is_temporary:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Temporary accounts cannot login. Please convert your account first.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not db_user.password_hash or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": str(db_user.id)})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    return current_user


# Temporary account endpoints
@app.post("/api/temp-account", response_model=Token)
async def create_temp_account(db: Session = Depends(get_db)):
    """Create a temporary account and return a token"""
    temp_user = create_temporary_account(db)
    access_token = create_access_token(data={"sub": str(temp_user.id)})
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/api/convert-account", response_model=UserResponse, status_code=200)
async def convert_account(
    account_data: AccountConvert,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Convert a temporary account to a permanent account"""
    # Verify current user is temporary
    user_id = current_user["id"]
    db_user = db.query(User).filter(User.id == user_id).first()
    
    if not db_user or not db_user.is_temporary:
        raise HTTPException(
            status_code=400,
            detail="Account is not temporary or does not exist"
        )
    
    # Check if username exists
    existing_user = db.query(User).filter(User.username == account_data.username).first()
    if existing_user and existing_user.id != user_id:
        raise HTTPException(status_code=400, detail="Username already taken")
    
    # Check if email exists
    existing_email = db.query(User).filter(User.email == account_data.email).first()
    if existing_email and existing_email.id != user_id:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Update user to permanent account
    db_user.username = account_data.username
    db_user.email = account_data.email
    db_user.password_hash = get_password_hash(account_data.password)
    db_user.is_temporary = False
    
    db.commit()
    db.refresh(db_user)
    
    return {
        "id": db_user.id,
        "username": db_user.username,
        "email": db_user.email,
        "is_temporary": db_user.is_temporary,
        "is_premium": db_user.is_premium
    }


# Admin endpoint to view all users (for debugging - remove in production)
@app.get("/api/users")
async def get_all_users(db: Session = Depends(get_db)):
    """Get all users - for debugging purposes only"""
    users = db.query(User).order_by(User.created_at.desc()).all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "is_temporary": u.is_temporary
        }
        for u in users
    ]


# Meal endpoints (protected)
@app.get("/api/meals", response_model=List[MealResponse])
async def get_meals(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all meals for the current user"""
    meals = db.query(Meal).filter(
        Meal.user_id == current_user["id"]
    ).order_by(Meal.created_at.desc()).all()
    
    return meals


@app.get("/api/meals/{meal_id}", response_model=MealResponse)
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


@app.post("/api/meals", response_model=MealResponse, status_code=201)
async def create_meal(
    meal: MealCreate,
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


@app.put("/api/meals/{meal_id}", response_model=MealResponse)
async def update_meal(
    meal_id: int,
    meal: MealUpdate,
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


# Maximum file size: 10MB
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes

@app.post("/api/meals/upload-photo")
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
    
    # Upload to MinIO
    try:
        filename = upload_photo(file_content, file_ext)
        return {"filename": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload photo: {str(e)}")


@app.post("/api/meals/extract-text-from-photo")
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
        # Open image with PIL
        image = Image.open(BytesIO(file_content))
        
        # Extract text using OCR
        extracted_text = pytesseract.image_to_string(image)
        
        # Clean up the text (remove extra whitespace)
        extracted_text = extracted_text.strip()
        
        # Upload photo to MinIO
        file_ext = Path(file.filename).suffix if file.filename else '.jpg'
        if not file_ext:
            file_ext = '.jpg'
        filename = upload_photo(file_content, file_ext)
        
        return {
            "filename": filename,
            "extracted_text": extracted_text
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to process photo: {str(e)}"
        )


@app.delete("/api/meals/{meal_id}", status_code=204)
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


@app.get("/api/meals/{meal_id}/photo")
async def get_meal_photo(
    meal_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get meal photo URL"""
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
