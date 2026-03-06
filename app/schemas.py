from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime

from app.validators import (
    validate_meal_name,
    validate_description,
    validate_url,
    sanitize_filename,
)


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
    photos: Optional[List[dict]] = None  # Array of photo objects: [{"filename": "...", "is_primary": true}, ...]


class MealUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    photo_filename: Optional[str] = None
    photos: Optional[List[dict]] = None  # Array of photo objects: [{"filename": "...", "is_primary": true}, ...]
    
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

    class Config:
        from_attributes = True
