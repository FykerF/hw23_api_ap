from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status

from sqlalchemy.orm import Session
from api.models.user import User
from api.models.links import Link
from services.link_services import (
    create_link, get_link_by_short_code, update_link, 
    delete_link, search_links_by_original_url, 
    get_link_stats, record_link_access, get_original_url_for_redirect
)
from services.shortcode_generator import is_custom_alias_available, validate_custom_alias
from utils.validators import validate_url

async def create_short_link(
    db: Session,
    original_url: str,
    current_user: Optional[User] = None,
    custom_alias: Optional[str] = None,
    expires_at: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Create a short link
    
    Args:
        db: Database session
        original_url: The URL to shorten
        current_user: Optional current user
        custom_alias: Optional custom alias
        expires_at: Optional expiration date
        
    Returns:
        New link data
    """
    # Validate URL
    if not validate_url(original_url):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid URL format"
        )
    
    # If custom alias is provided, validate and check availability
    if custom_alias:
        if not validate_custom_alias(custom_alias):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid custom alias format"
            )
            
        if not is_custom_alias_available(db, custom_alias):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Custom alias already in use"
            )
    
    # Get user ID if user is authenticated
    user_id = current_user.id if current_user else None
    
    # Create link
    link = await create_link(db, original_url, user_id, custom_alias, expires_at)
    
    return link.to_dict()

async def get_link_info(db: Session, short_code: str, current_user: Optional[User] = None) -> Dict[str, Any]:
    """
    Get link information
    
    Args:
        db: Database session
        short_code: The short code to look up
        current_user: Optional current user
        
    Returns:
        Link data
    """
    # Get link
    link = await get_link_by_short_code(db, short_code)
    
    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link not found"
        )
    
    # Check if link is active
    if not link.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link is inactive"
        )
    
    # Check if link is expired
    if link.is_expired:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link has expired"
        )
    
    return link.to_dict()

async def update_link_info(
    db: Session,
    short_code: str,
    original_url: Optional[str] = None,
    expires_at: Optional[datetime] = None,
    current_user: Optional[User] = None
) -> Dict[str, Any]:
    """
    Update link information
    
    Args:
        db: Database session
        short_code: The short code to update
        original_url: Optional new original URL
        expires_at: Optional new expiration date
        current_user: Optional current user
        
    Returns:
        Updated link data
    """
    # Get link
    link = await get_link_by_short_code(db, short_code)
    
    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link not found"
        )
    
    # Check if user is authorized to update this link
    if link.user_id and current_user and link.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this link"
        )
    
    # If anonymous link and no user is provided, disallow update
    if not link.user_id and not current_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this link"
        )
    
    # Validate new URL if provided
    if original_url and not validate_url(original_url):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid URL format"
        )
    
    # Update link
    updated_link = await update_link(db, link, original_url, expires_at)
    
    return updated_link.to_dict()

async def delete_link_by_short_code(
    db: Session,
    short_code: str,
    current_user: Optional[User] = None
) -> Dict[str, Any]:
    """
    Delete a link
    
    Args:
        db: Database session
        short_code: The short code to delete
        current_user: Optional current user
        
    Returns:
        Status message
    """
    # Get link
    link = await get_link_by_short_code(db, short_code)
    
    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link not found"
        )
    
    # Check if user is authorized to delete this link
    if link.user_id and current_user and link.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this link"
        )
    
    # If anonymous link and no user is provided, disallow deletion
    if not link.user_id and not current_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this link"
        )
    
    # Delete link
    success = await delete_link(db, link)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete link"
        )
    
    return {"detail": "Link deleted successfully"}

async def get_link_statistics(db: Session, short_code: str, current_user: Optional[User] = None) -> Dict[str, Any]:
    """
    Get link statistics
    
    Args:
        db: Database session
        short_code: The short code to get stats for
        current_user: Optional current user
        
    Returns:
        Link statistics
    """
    # Get link
    link = await get_link_by_short_code(db, short_code)
    
    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link not found"
        )
    
    # Get link statistics
    stats = await get_link_stats(db, link)
    
    return stats

async def search_links(
    db: Session,
    original_url: str,
    current_user: Optional[User] = None
) -> List[Dict[str, Any]]:
    """
    Search for links by original URL
    
    Args:
        db: Database session
        original_url: The original URL to search for
        current_user: Optional current user
        
    Returns:
        List of matching links
    """
    # Get user ID if user is authenticated
    user_id = current_user.id if current_user else None
    
    # Search for links
    links = await search_links_by_original_url(db, original_url, user_id)
    
    return [link.to_dict() for link in links]

async def get_original_url(short_code: str, ip_address: str) -> str:
    """
    Get original URL for redirect
    
    Args:
        short_code: The short code to redirect
        ip_address: The IP address making the request
        
    Returns:
        Original URL
    """
    from core.database import SessionLocal
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Get link
        link = await get_link_by_short_code(db, short_code)
        
        if not link:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Link not found"
            )
        
        # Check if link is active
        if not link.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Link is inactive"
            )
        
        # Check if link is expired
        if link.expires_at:
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc)
            if now > link.expires_at:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Link has expired"
                )
        
        # Record access
        await record_link_access(db, link, ip_address)
        
        # Return original URL
        return link.original_url
        
    finally:
        db.close()