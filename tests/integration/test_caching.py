import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session
import time
from unittest.mock import patch, AsyncMock
import asyncio

from core.redis_client import get_cached_link, cache_link
from api.controllers.link_controller import get_original_url

@pytest.mark.asyncio
async def test_cached_redirect_performance(client: AsyncClient, db_session: Session):
    """Test that cached redirects are faster than uncached ones"""
    # Create a link through the API
    create_response = await client.post(
        "/links/shorten",
        json={
            "original_url": "https://example.com/cached-perf-test"
        }
    )
    
    assert create_response.status_code == 200
    short_code = create_response.json()["short_code"]
    
    # Clear the cache if the link was automatically cached during creation
    await cache_link(short_code, None)
    
    # First redirect (uncached) - measure time
    start_time_uncached = time.time()
    await client.get(f"/{short_code}", follow_redirects=False)
    uncached_time = time.time() - start_time_uncached
    
    # Wait a moment for the cache to be updated
    await asyncio.sleep(0.1)
    
    # Second redirect (should be cached) - measure time
    start_time_cached = time.time()
    await client.get(f"/{short_code}", follow_redirects=False)
    cached_time = time.time() - start_time_cached
    
    # Verify that cached redirect is faster
    # Note: This test might be flaky depending on system load, but should work most of the time
    assert cached_time < uncached_time, f"Cached time ({cached_time}s) should be less than uncached time ({uncached_time}s)"

@pytest.mark.asyncio
async def test_redirect_uses_cache(client: AsyncClient, db_session: Session):
    """Test that redirect uses cache when available and falls back to database when not"""
    # Create a link through the API
    create_response = await client.post(
        "/links/shorten",
        json={
            "original_url": "https://example.com/original-url"
        }
    )
    
    assert create_response.status_code == 200
    short_code = create_response.json()["short_code"]
    original_url = create_response.json()["original_url"]
    
    # Clear any existing cache
    await cache_link(short_code, None)
    
    # Use a separate cache entry with modified URL
    modified_url = "https://example.com/modified-in-cache"
    await cache_link(short_code, modified_url)
    
    # Get cached URL and verify it matches our modified URL
    cached_url = await get_cached_link(short_code)
    assert cached_url == modified_url
    
    # Test redirect - should use cached value (modified URL)
    response = await client.get(f"/{short_code}", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == modified_url
    
    # Clear cache again
    await cache_link(short_code, None)
    
    # Test redirect - should now use database value (original URL)
    response = await client.get(f"/{short_code}", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == original_url

@pytest.mark.asyncio
@patch('api.controllers.link_controller.get_cached_link')
@patch('api.controllers.link_controller.cache_link')
async def test_redirect_updates_cache_on_miss(mock_cache_link, mock_get_cached_link, client: AsyncClient, db_session: Session):
    """Test that a cache miss triggers a cache update after database lookup"""
    # Create a link through the API
    create_response = await client.post(
        "/links/shorten",
        json={
            "original_url": "https://example.com/cache-miss-test"
        }
    )
    
    assert create_response.status_code == 200
    short_code = create_response.json()["short_code"]
    original_url = create_response.json()["original_url"]
    
    # Mock the cache miss
    mock_get_cached_link.return_value = None
    
    # Access the link
    response = await client.get(f"/{short_code}", follow_redirects=False)
    
    # Verify the redirect worked
    assert response.status_code == 307
    assert response.headers["location"] == original_url
    
    # Verify cache was checked
    mock_get_cached_link.assert_called_once_with(short_code)
    
    # Verify cache was updated after database lookup
    mock_cache_link.assert_called_once()
    args, kwargs = mock_cache_link.call_args
    assert args[0] == short_code
    assert args[1] == original_url