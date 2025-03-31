import pytest
from httpx import AsyncClient
from fastapi import status
from datetime import datetime, timedelta
import uuid
from unittest.mock import patch

@pytest.mark.asyncio
async def test_redirect_to_original_url(client: AsyncClient):
    """Test redirect from short code to original URL"""
    # Create a link
    response = await client.post(
        "/links/shorten",
        json={
            "original_url": "https://example.com/redirect-test"
        }
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    short_code = data["short_code"]
    
    # Test redirect
    response = await client.get(f"/{short_code}", follow_redirects=False)
    
    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert response.headers["location"] == "https://example.com/redirect-test"

@pytest.mark.asyncio
async def test_redirect_nonexistent_link(client: AsyncClient):
    """Test redirect with nonexistent short code"""
    response = await client.get("/nonexistentcode", follow_redirects=False)
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_redirect_expired_link(client: AsyncClient):
    """Test redirect with expired link"""
    # Create a link that expires immediately
    response = await client.post(
        "/links/shorten",
        json={
            "original_url": "https://example.com/expired",
            "expires_at": (datetime.now() - timedelta(days=1)).isoformat()  # Already expired
        }
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    short_code = data["short_code"]
    
    # Test redirect to expired link
    response = await client.get(f"/{short_code}", follow_redirects=False)
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_redirect_updates_stats(client: AsyncClient, auth_headers):
    """Test that redirect updates link statistics"""
    # Create a link
    response = await client.post(
        "/links/shorten",
        json={
            "original_url": "https://example.com/stats-update-test"
        },
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    short_code = data["short_code"]
    
    # Get initial stats
    response = await client.get(f"/links/{short_code}/stats", headers=auth_headers)
    initial_access_count = response.json()["access_count"]
    
    # Access the link multiple times
    for _ in range(3):
        await client.get(f"/{short_code}", follow_redirects=False)
    
    # Get updated stats
    response = await client.get(f"/links/{short_code}/stats", headers=auth_headers)
    updated_access_count = response.json()["access_count"]
    
    # Verify access count increased
    assert updated_access_count >= initial_access_count + 3

@pytest.mark.asyncio
@patch('api.controllers.link_controller.get_cached_link')
async def test_redirect_uses_cache(mock_get_cached_link, client: AsyncClient):
    """Test that redirect uses Redis cache when available"""
    # Mock cache to return a URL
    mock_get_cached_link.return_value = "https://example.com/cached"
    
    # Access a link (should use the cache)
    response = await client.get("/cachedcode", follow_redirects=False)
    
    # Verify redirect worked with cached URL
    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert response.headers["location"] == "https://example.com/cached"
    
    # Verify cache was checked
    mock_get_cached_link.assert_called_once_with("cachedcode")