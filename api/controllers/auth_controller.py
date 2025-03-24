import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from api.models.user import User
from core.config import settings
from core.database import get_db
from core.redis_client import redis_client, AUTH_PREFIX

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for JWT token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return pwd_context.hash(password)

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get a user by email"""
    return db.query(User).filter(User.email == email).first()

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get a user by username"""
    return db.query(User).filter(User.username == username).first()

def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
    """Get a user by ID"""
    return db.query(User).filter(User.id == user_id).first()

def create_user(db: Session, username: str, email: str, password: str) -> User:
    """Create a new user"""
    # Generate user ID
    user_id = str(uuid.uuid4())
    
    # Hash password
    hashed_password = get_password_hash(password)
    
    # Create user
    db_user = User(
        id=user_id,
        username=username,
        email=email,
        password_hash=hashed_password
    )
    
    # Add to database
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate a user"""
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    
    return encoded_jwt

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Get current user from JWT token"""
    from core.redis_client import get_redis, AUTH_PREFIX  # Add this import
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode JWT token
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
            
        # Check if token is blacklisted (for logout)
        redis = await get_redis()  # Get Redis client
        if redis:  # Only check if Redis is available
            token_blacklisted = await redis.exists(f"{AUTH_PREFIX}blacklist:{token}")
            if token_blacklisted:
                raise credentials_exception
            
    except JWTError:
        raise credentials_exception
        
    # Get user from database
    user = get_user_by_id(db, user_id)
    if user is None:
        raise credentials_exception
        
    return user

async def get_optional_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user if available, otherwise None"""
    if token is None:
        return None
        
    try:
        return await get_current_user(token, db)
    except HTTPException:
        return None

async def blacklist_token(token: str) -> bool:
    """Blacklist a token (for logout)"""
    from core.redis_client import get_redis, AUTH_PREFIX  # Add this import
    
    # Get Redis client
    redis = await get_redis()
    if not redis:
        return False
        
    # Decode token to get expiration time
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        exp = payload.get("exp")
        
        if exp:
            # Calculate time until expiration
            exp_datetime = datetime.fromtimestamp(exp)
            current_datetime = datetime.utcnow()
            ttl = (exp_datetime - current_datetime).total_seconds()
            
            if ttl > 0:
                # Add token to blacklist with TTL until its expiration
                await redis.setex(f"{AUTH_PREFIX}blacklist:{token}", int(ttl), "1")
                return True
    except:
        pass
        
    return False