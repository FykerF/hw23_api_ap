from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from api.controllers.link_controller import (
    create_short_link, get_link_info, update_link_info,
    delete_link_by_short_code, get_link_statistics, search_links
)
from api.controllers.auth_controller import get_current_user, get_optional_current_user
from api.models.user import User
from core.database import get_db

# Pydantic models for requests and responses
from pydantic import BaseModel, HttpUrl, validator
from typing import Dict, Any, Optional

class LinkCreate(BaseModel):
    original_url: str
    custom_alias: Optional[str] = None
    expires_at: Optional[datetime] = None

class LinkUpdate(BaseModel):
    original_url: Optional[str] = None
    expires_at: Optional[datetime] = None

class LinkResponse(BaseModel):
    short_code: str
    short_url: str
    original_url: str
    created_at: str
    expires_at: Optional[str] = None
    access_count: Optional[int] = None
    last_accessed_at: Optional[str] = None

class LinkStatsResponse(BaseModel):
    short_code: str
    original_url: str
    created_at: str
    access_count: int
    last_accessed_at: Optional[str] = None

class LinkSearchResponse(BaseModel):
    links: List[LinkResponse]

router = APIRouter()

@router.post("/shorten", response_model=LinkResponse)
async def shorten_url(
    link_data: LinkCreate,
    db: Session = Depends(get_db),
    # Make sure authentication is truly optional
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """
    Create a short URL.
    Authentication is optional for this endpoint.
    """
    try:
        link = await create_short_link(
            db,
            original_url=link_data.original_url,
            current_user=current_user,
            custom_alias=link_data.custom_alias,
            expires_at=link_data.expires_at
        )
        return link
    except Exception as e:
        # Log the error for debugging
        print(f"Error creating short link: {str(e)}")
        raise

@router.get("/{short_code}", response_model=LinkResponse)
async def get_link(
    short_code: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """
    Get information about a short URL
    """
    link = await get_link_info(db, short_code, current_user)
    return link

@router.put("/{short_code}", response_model=LinkResponse)
async def update_link(
    short_code: str,
    link_data: LinkUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a short URL
    Requires authentication
    """
    link = await update_link_info(
        db,
        short_code=short_code,
        original_url=link_data.original_url,
        expires_at=link_data.expires_at,
        current_user=current_user
    )
    
    return link

@router.delete("/{short_code}")
async def delete_link(
    short_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a short URL
    Requires authentication
    """
    result = await delete_link_by_short_code(db, short_code, current_user)
    return result

@router.get("/{short_code}/stats", response_model=LinkStatsResponse)
async def get_stats(
    short_code: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """
    Get statistics for a short URL
    """
    stats = await get_link_statistics(db, short_code, current_user)
    return stats

@router.get("/search", response_model=LinkSearchResponse)
async def search_urls(
    original_url: str = Query(..., description="Original URL to search for"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """
    Search for short URLs by original URL
    """
    links = await search_links(db, original_url, current_user)
    return {"links": links}