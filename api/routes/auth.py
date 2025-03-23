from datetime import timedelta
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from api.controllers.auth_controller import (
    authenticate_user, create_access_token, create_user, 
    get_current_user, get_user_by_email, get_user_by_username,
    blacklist_token
)
from api.models.user import User
from core.config import settings
from core.database import get_db

# Pydantic models for requests and responses
from pydantic import BaseModel, EmailStr, validator

class Token(BaseModel):
    access_token: str
    token_type: str

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    
    @validator('username')
    def username_must_be_valid(cls, v):
        if len(v) < 3 or len(v) > 20:
            raise ValueError('Username must be between 3 and 20 characters')
        if not v.isalnum() and '_' not in v and '-' not in v:
            raise ValueError('Username must contain only alphanumeric characters, underscores, or hyphens')
        return v
        
    @validator('password')
    def password_must_be_strong(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v

class UserResponse(BaseModel):
    id: str
    username: str
    email: EmailStr

router = APIRouter()

@router.post("/register", response_model=UserResponse)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    # Check if email already exists
    if get_user_by_email(db, user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
        
    # Check if username already exists
    if get_user_by_username(db, user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
        
    # Create user
    user = create_user(
        db, 
        username=user_data.username,
        email=user_data.email,
        password=user_data.password
    )
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email
    }

@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    # Authenticate user
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # Create access token
    access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    token: str = Depends(OAuth2PasswordRequestForm)
):
    # Blacklist the token
    await blacklist_token(token)
    return {"detail": "Successfully logged out"}

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email
    }