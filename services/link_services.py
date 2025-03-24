import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from api.models.links import Link
from services.shortcode_generator import generate_short_code, is_custom_alias_available
from core.redis_client import (
    cache_link, delete_cached_link, get_cached_link,
    increment_link_access, cache_link_stats, get_cached_link_stats
)

async def create_link(
    db: Session,
    original_url: str,
    user_id: Optional[str] = None,
    custom_alias: Optional[str] = None,
    expires_at: Optional[datetime] = None
) -> Link:
    """
    Create a new shortened link
    
    Args:
        db: Database session
        original_url: The original URL to shorten
        user_id: Optional user ID for the link owner
        custom_alias: Optional custom alias for the link
        expires_at: Optional expiration date for the link
        
    Returns:
        The newly created Link object
    """
    # Generate link ID
    link_id = str(uuid.uuid4())
    
    # Use custom alias or generate short code
    short_code = custom_alias if custom_alias else generate_short_code(db)
    
    # Create new link
    link = Link(
        id=link_id,
        original_url=original_url,
        short_code=short_code,
        custom_alias=custom_alias,
        user_id=user_id,
        expires_at=expires_at
    )
    
    # Add to database
    db.add(link)
    db.commit()
    db.refresh(link)
    
    # Cache the link for faster redirects
    await cache_link(short_code, original_url, expires_at)
    
    return link

async def get_link_by_short_code(db: Session, short_code: str) -> Optional[Link]:
    """
    Get a link by its short code
    
    Args:
        db: Database session
        short_code: The short code to look up
        
    Returns:
        The Link object if found, None otherwise
    """
    return db.query(Link).filter(Link.short_code == short_code).first()

async def get_link_by_id(db: Session, link_id: str) -> Optional[Link]:
    """
    Get a link by its ID
    
    Args:
        db: Database session
        link_id: The link ID to look up
        
    Returns:
        The Link object if found, None otherwise
    """
    return db.query(Link).filter(Link.id == link_id).first()

async def search_links_by_original_url(
    db: Session, 
    original_url: str, 
    user_id: Optional[str] = None
) -> List[Link]:
    """
    Search for links by their original URL
    
    Args:
        db: Database session
        original_url: The original URL to search for
        user_id: Optional user ID to filter by
        
    Returns:
        A list of matching Link objects
    """
    query = db.query(Link).filter(Link.original_url.contains(original_url))
    
    # If user_id is provided, filter links by user_id
    if user_id:
        query = query.filter(Link.user_id == user_id)
    
    return query.all()

async def update_link(
    db: Session, 
    link: Link, 
    original_url: Optional[str] = None,
    expires_at: Optional[datetime] = None
) -> Link:
    """
    Update a link's properties
    
    Args:
        db: Database session
        link: The Link object to update
        original_url: Optional new original URL
        expires_at: Optional new expiration date
        
    Returns:
        The updated Link object
    """
    # Update link properties
    if original_url is not None:
        link.original_url = original_url
    
    if expires_at is not None:
        link.expires_at = expires_at
    
    # Update in database
    db.commit()
    db.refresh(link)
    
    # Update cache
    await delete_cached_link(link.short_code)
    await cache_link(link.short_code, link.original_url, link.expires_at)
    
    return link

async def delete_link(db: Session, link: Link) -> bool:
    """
    Delete a link
    
    Args:
        db: Database session
        link: The Link object to delete
        
    Returns:
        True if deletion was successful
    """
    # Delete from database
    db.delete(link)
    db.commit()
    
    # Delete from cache
    await delete_cached_link(link.short_code)
    
    return True

async def record_link_access(db: Session, link: Link, ip_address: str) -> Link:
    """
    Record access to a link
    
    Args:
        db: Database session
        link: The Link that was accessed
        ip_address: The IP address that accessed the link
        
    Returns:
        The updated Link object
    """
    # Update link stats
    link.access_count += 1
    link.last_accessed_at = datetime.now()
    
    # Update in database
    db.commit()
    db.refresh(link)
    
    # Update cache counter
    await increment_link_access(link.short_code)
    
    # Could also add IP tracking for more detailed analytics
    
    return link

async def get_link_stats(db: Session, link: Link) -> Dict[str, Any]:
    """
    Get statistics for a link
    
    Args:
        db: Database session
        link: The Link to get stats for
        
    Returns:
        A dictionary with link statistics
    """
    # Try to get stats from cache first
    cached_stats = await get_cached_link_stats(link.short_code)
    if cached_stats:
        return cached_stats
    
    # If not in cache, get from database and cache it
    stats = link.to_stats_dict()
    await cache_link_stats(link.short_code, stats)
    
    return stats

async def get_original_url_for_redirect(db: Session, short_code: str) -> Optional[str]:
    """
    Get the original URL for a redirect operation with caching
    
    Args:
        db: Database session
        short_code: The short code to redirect
        
    Returns:
        The original URL if found, None otherwise
    """
    # Try to get from cache first for performance
    cached_url = await get_cached_link(short_code)
    if cached_url:
        return cached_url
    
    # If not in cache, get from database
    link = await get_link_by_short_code(db, short_code)
    
    if not link or not link.is_active:
        return None
        
    if link.is_expired:
        return None
    
    # Cache for future requests
    await cache_link(short_code, link.original_url, link.expires_at)
    
    return link.original_url

async def cleanup_expired_links(db: Session) -> int:
    """
    Clean up expired links
    
    Args:
        db: Database session
        
    Returns:
        Number of links cleaned up
    """
    now = datetime.now(timezone.utc)
    expired_links = db.query(Link).filter(
        and_(
            Link.expires_at.isnot(None),
            Link.expires_at < now
        )
    ).all()
    
    count = 0
    for link in expired_links:
        await delete_link(db, link)
        count += 1
    
    return count

async def cleanup_unused_links(db: Session, days: int) -> int:
    """
    Clean up links that haven't been used for a specified number of days
    
    Args:
        db: Database session
        days: Number of days of inactivity
        
    Returns:
        Number of links cleaned up
    """
    from datetime import timedelta
    
    cutoff_date = datetime.now() - timedelta(days=days)
    unused_links = db.query(Link).filter(
        or_(
            Link.last_accessed_at < cutoff_date,
            and_(
                Link.last_accessed_at.is_(None),
                Link.created_at < cutoff_date
            )
        )
    ).all()
    
    count = 0
    for link in unused_links:
        await delete_link(db, link)
        count += 1
    
    return count