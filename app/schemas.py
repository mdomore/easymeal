from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


# Auth / User schemas
class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    username: str  # Can be username or email
    password: str


class UserResponse(BaseModel):
    id: Optional[int] = None
    username: Optional[str] = None
    email: Optional[str] = None
    is_temporary: Optional[bool] = None
    is_premium: Optional[bool] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


# Meal schemas
class MealBase(BaseModel):
    name: str
    description: Optional[str] = None
    url: Optional[str] = None
    photo_filename: Optional[str] = None


class MealCreate(MealBase):
    pass


class MealUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    photo_filename: Optional[str] = None


class MealResponse(MealBase):
    id: Optional[int] = None
    photos: Optional[list] = None  # Array of photo objects: [{"filename": "...", "is_primary": true}, ...]
    created_at: Optional[datetime] = None
    user_id: Optional[int] = None

    class Config:
        from_attributes = True
