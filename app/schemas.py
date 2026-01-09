from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime

from app.validators import (
    validate_username, validate_password, validate_meal_name,
    validate_description, validate_url, sanitize_filename
)


# Auth / User schemas
class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    
    @field_validator('username')
    @classmethod
    def validate_username_field(cls, v: str) -> str:
        return validate_username(v)
    
    @field_validator('password')
    @classmethod
    def validate_password_field(cls, v: str) -> str:
        return validate_password(v)


class UserLogin(BaseModel):
    username: str  # Can be username or email
    password: str
    
    @field_validator('password')
    @classmethod
    def validate_password_field(cls, v: str) -> str:
        return validate_password(v)


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
    csrf_token: Optional[str] = None  # CSRF token for state-changing operations


# Meal schemas
class MealBase(BaseModel):
    name: str
    description: Optional[str] = None
    url: Optional[str] = None
    photo_filename: Optional[str] = None
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        return validate_meal_name(v)
    
    @field_validator('description')
    @classmethod
    def validate_description_field(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return validate_description(v)
    
    @field_validator('url')
    @classmethod
    def validate_url_field(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return validate_url(v)
    
    @field_validator('photo_filename')
    @classmethod
    def validate_photo_filename(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return sanitize_filename(v)


class MealCreate(MealBase):
    pass


class MealUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    photo_filename: Optional[str] = None
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return validate_meal_name(v)
    
    @field_validator('description')
    @classmethod
    def validate_description_field(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return validate_description(v)
    
    @field_validator('url')
    @classmethod
    def validate_url_field(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return validate_url(v)
    
    @field_validator('photo_filename')
    @classmethod
    def validate_photo_filename(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return sanitize_filename(v)


class MealResponse(MealBase):
    id: Optional[int] = None
    photos: Optional[list] = None  # Array of photo objects: [{"filename": "...", "is_primary": true}, ...]
    created_at: Optional[datetime] = None
    user_id: Optional[int] = None

    class Config:
        from_attributes = True
