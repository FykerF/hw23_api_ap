import pytest
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient
from fastapi import status
from sqlalchemy.orm import Session

from api.models.links import Link
from services.cleanup_service import cleanup_expired_links, cleanup_unused_links

@pytest.mark.asyncio
async def test_cleanup_expired_links(client: AsyncClient, db_session: Session):
    """Test cleanup of expired links"""
    # Create several links with different expiration times
    now = datetime.now(timezone.utc)
    
    # Create expired link
    expired_link = Link(
        id="test-expired-id",
        original_url="https://example.com/expired",
        short_code="expired",
        created_at=now - timedelta(days=10),
        expires_at=now - timedelta(days=1)  # Already expired
    )
    
    # Create link that expires soon
    expiring_link = Link(
        id="test-expiring-id",
        original_url="https://example.com/expiring",
        short_code="expiring",
        created_at=now - timedelta(days=5),
        expires_at=now + timedelta(hours=1)  # Expires soon but still valid
    )
    
    # Create link with no expiration
    no_expiry_link = Link(
        id="test-noexpiry-id",
        original_url="https://example.com/noexpiry",
        short_code="noexpiry",
        created_at=now - timedelta(days=5)
        # No expires_at
    )
    
    # Add to database
    db_session.add(expired_link)
    db_session.add(expiring_link)
    db_session.add(no_expiry_link)
    db_session.commit()
    
    # Run cleanup
    cleaned_count = await cleanup_expired_links(db_session)
    
    # Verify only expired link was cleaned up
    assert cleaned_count == 1
    
    # Check that expired link no longer exists
    expired_check = db_session.query(Link).filter(Link.short_code == "expired").first()
    assert expired_check is None
    
    # Check that non-expired links still exist
    expiring_check = db_session.query(Link).filter(Link.short_code == "expiring").first()
    no_expiry_check = db_session.query(Link).filter(Link.short_code == "noexpiry").first()
    
    assert expiring_check is not None
    assert no_expiry_check is not None

@pytest.mark.asyncio
async def test_cleanup_unused_links(client: AsyncClient, db_session: Session):
    """Test cleanup of unused links"""
    # Create several links with different last access times
    now = datetime.now(timezone.utc)
    
    # Create unused link (old)
    unused_link = Link(
        id="test-unused-id",
        original_url="https://example.com/unused",
        short_code="unused",
        created_at=now - timedelta(days=100),
        last_accessed_at=now - timedelta(days=90)  # Last accessed 90 days ago
    )
    
    # Create recently used link
    recent_link = Link(
        id="test-recent-id",
        original_url="https://example.com/recent",
        short_code="recent",
        created_at=now - timedelta(days=100),
        last_accessed_at=now - timedelta(days=5)  # Last accessed 5 days ago
    )
    
    # Create new link never accessed
    new_link = Link(
        id="test-new-id",
        original_url="https://example.com/new",
        short_code="new",
        created_at=now - timedelta(days=5)
        # No last_accessed_at
    )
    
    # Add to database
    db_session.add(unused_link)
    db_session.add(recent_link)
    db_session.add(new_link)
    db_session.commit()
    
    # Run cleanup (with 30-day threshold)
    cleaned_count = await cleanup_unused_links(db_session, 30)
    
    # Verify only unused link was cleaned up
    assert cleaned_count == 1
    
    # Check that unused link no longer exists
    unused_check = db_session.query(Link).filter(Link.short_code == "unused").first()
    assert unused_check is None
    
    # Check that other links still exist
    recent_check = db_session.query(Link).filter(Link.short_code == "recent").first()
    new_check = db_session.query(Link).filter(Link.short_code == "new").first()
    
    assert recent_check is not None
    assert new_check is not None