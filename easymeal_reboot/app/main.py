from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime, timedelta
import sqlite3
import os
from jose import JWTError, jwt
import bcrypt

app = FastAPI(title="EasyMeal Recipe App", version="1.0.0")

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

# Database path
DB_PATH = os.getenv("DB_PATH", "meals.db")


# Pydantic models
class User(BaseModel):
    id: Optional[int] = None
    username: str
    email: str

    class Config:
        from_attributes = True


class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class Meal(BaseModel):
    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    url: Optional[str] = None
    created_at: Optional[str] = None
    user_id: Optional[int] = None

    class Config:
        from_attributes = True


class MealCreate(BaseModel):
    name: str
    description: Optional[str] = None
    url: Optional[str] = None


class MealUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None


# Database initialization
def init_db():
    # Ensure the directory exists
    db_dir = os.path.dirname(DB_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    
    # Meals table with user_id
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS meals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            url TEXT,
            created_at TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # Add url column if it doesn't exist (for existing databases)
    cursor.execute("PRAGMA table_info(meals)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'url' not in columns:
        cursor.execute("ALTER TABLE meals ADD COLUMN url TEXT")
    
    conn.commit()
    conn.close()


# Password hashing
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def get_password_hash(password: str) -> str:
    # Hash password with bcrypt
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


# Authentication dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        if credentials is None:
            print("ERROR: No credentials provided")
            raise credentials_exception
            
        token = credentials.credentials
        print(f"DEBUG: Received token (first 30 chars): {token[:30] if token else 'None'}...")
        
        if not token:
            print("ERROR: Empty token")
            raise credentials_exception
        
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            print(f"DEBUG: JWT payload decoded successfully: {payload}")
        except JWTError as jwt_err:
            print(f"ERROR: JWT decode failed: {jwt_err}")
            raise credentials_exception
        
        user_id_str = payload.get("sub")
        if user_id_str is None:
            print(f"ERROR: No user_id in token payload: {payload}")
            raise credentials_exception
        
        # Convert string user_id back to integer for database lookup
        try:
            user_id = int(user_id_str)
            print(f"DEBUG: Decoded user_id: {user_id}, type: {type(user_id)}")
        except (ValueError, TypeError):
            print(f"ERROR: Invalid user_id format: {user_id_str}")
            raise credentials_exception
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        print(f"ERROR: Unexpected auth error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise credentials_exception
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, email FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row is None:
            print(f"ERROR: User not found in database for user_id: {user_id}")
            raise credentials_exception
        
        print(f"DEBUG: User found successfully: {dict(row)}")
        return dict(row)
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR: Database error: {e}")
        raise credentials_exception


@app.on_event("startup")
async def startup_event():
    init_db()


# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def read_root():
    return FileResponse("static/index.html")


# Authentication endpoints
@app.post("/api/register", response_model=User, status_code=201)
async def register(user: UserRegister):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if username exists
    cursor.execute("SELECT id FROM users WHERE username = ?", (user.username,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Check if email exists
    cursor.execute("SELECT id FROM users WHERE email = ?", (user.email,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Email already registered")
    
    password_hash = get_password_hash(user.password)
    created_at = datetime.now().isoformat()
    cursor.execute(
        "INSERT INTO users (username, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
        (user.username, user.email, password_hash, created_at)
    )
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {"id": user_id, "username": user.username, "email": user.email}


@app.post("/api/login", response_model=Token)
async def login(user: UserLogin):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (user.username,))
    row = cursor.fetchone()
    conn.close()
    
    if row is None or not verify_password(user.password, row["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = row["id"]
    # Ensure user_id is an integer, then convert to string for JWT (sub must be a string)
    if not isinstance(user_id, int):
        user_id = int(user_id)
    # JWT 'sub' claim must be a string
    access_token = create_access_token(data={"sub": str(user_id)})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/me", response_model=User)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    return current_user


# Admin endpoint to view all users (for debugging - remove in production)
@app.get("/api/users")
async def get_all_users():
    """Get all users - for debugging purposes only"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email, created_at FROM users ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    
    users = [dict(row) for row in rows]
    return users


# Meal endpoints (protected)
@app.get("/api/meals", response_model=List[Meal])
async def get_meals(current_user: dict = Depends(get_current_user)):
    """Get all meals for the current user"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM meals WHERE user_id = ? ORDER BY created_at DESC",
        (current_user["id"],)
    )
    rows = cursor.fetchall()
    conn.close()
    
    meals = [dict(row) for row in rows]
    return meals


@app.get("/api/meals/{meal_id}", response_model=Meal)
async def get_meal(meal_id: int, current_user: dict = Depends(get_current_user)):
    """Get a specific meal by ID"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM meals WHERE id = ? AND user_id = ?",
        (meal_id, current_user["id"])
    )
    row = cursor.fetchone()
    conn.close()
    
    if row is None:
        raise HTTPException(status_code=404, detail="Meal not found")
    
    return dict(row)


@app.post("/api/meals", response_model=Meal, status_code=201)
async def create_meal(meal: MealCreate, current_user: dict = Depends(get_current_user)):
    """Create a new meal"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    created_at = datetime.now().isoformat()
    cursor.execute(
        "INSERT INTO meals (name, description, url, created_at, user_id) VALUES (?, ?, ?, ?, ?)",
        (meal.name, meal.description, meal.url, created_at, current_user["id"])
    )
    meal_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {
        "id": meal_id,
        "name": meal.name,
        "description": meal.description,
        "url": meal.url,
        "created_at": created_at,
        "user_id": current_user["id"]
    }


@app.put("/api/meals/{meal_id}", response_model=Meal)
async def update_meal(
    meal_id: int,
    meal: MealUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a meal"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Check if meal exists and belongs to user
    cursor.execute(
        "SELECT * FROM meals WHERE id = ? AND user_id = ?",
        (meal_id, current_user["id"])
    )
    row = cursor.fetchone()
    
    if row is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Meal not found")
    
    # Update fields
    update_fields = []
    values = []
    if meal.name is not None:
        update_fields.append("name = ?")
        values.append(meal.name)
    if meal.description is not None:
        update_fields.append("description = ?")
        values.append(meal.description)
    if meal.url is not None:
        update_fields.append("url = ?")
        values.append(meal.url)
    
    if not update_fields:
        conn.close()
        return dict(row)
    
    values.extend([meal_id, current_user["id"]])
    cursor.execute(
        f"UPDATE meals SET {', '.join(update_fields)} WHERE id = ? AND user_id = ?",
        values
    )
    conn.commit()
    
    # Fetch updated meal
    cursor.execute(
        "SELECT * FROM meals WHERE id = ? AND user_id = ?",
        (meal_id, current_user["id"])
    )
    updated_row = cursor.fetchone()
    conn.close()
    
    return dict(updated_row)


@app.delete("/api/meals/{meal_id}", status_code=204)
async def delete_meal(meal_id: int, current_user: dict = Depends(get_current_user)):
    """Delete a meal by ID"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM meals WHERE id = ? AND user_id = ?",
        (meal_id, current_user["id"])
    )
    conn.commit()
    deleted = cursor.rowcount
    conn.close()
    
    if deleted == 0:
        raise HTTPException(status_code=404, detail="Meal not found")
    
    return None
