import pytest
from httpx import AsyncClient
from fastapi import status
from datetime import datetime, timedelta
import uuid
from unittest.mock import patch

@pytest.mark.asyncio
async def test_create_short_link_authenticated(client: AsyncClient, auth_headers):
    """Test creating a short link with authentication"""
    response = await client.post(
        "/links/shorten",
        json={
            "original_url": "https://example.com/test",
            "expires_at": (datetime.now() + timedelta(days=1)).isoformat()
        },
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "short_code" in data
    assert "short_url" in data
    assert data["original_url"] == "https://example.com/test"
    
    # Save short_code for later tests
    return data["short_code"]

@pytest.mark.asyncio
async def test_create_short_link_anonymous(client: AsyncClient):
    """Test creating a short link without authentication"""
    response = await client.post(
        "/links/shorten",
        json={
            "original_url": "https://example.com/anonymous"
        }
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "short_code" in data
    assert data["original_url"] == "https://example.com/anonymous"

@pytest.mark.asyncio
async def test_create_short_link_with_custom_alias(client: AsyncClient, auth_headers):
    """Test creating a short link with custom alias"""
    custom_alias = f"test-{uuid.uuid4().hex[:8]}"  # Generate unique alias for test
    
    response = await client.post(
        "/links/shorten",
        json={
            "original_url": "https://example.com/custom",
            "custom_alias": custom_alias
        },
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["short_code"] == custom_alias
    assert data["original_url"] == "https://example.com/custom"
    
    # Verify that using the same alias again fails
    response = await client.post(
        "/links/shorten",
        json={
            "original_url": "https://example.com/another",
            "custom_alias": custom_alias
        },
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "already in use" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_create_short_link_invalid_url(client: AsyncClient, auth_headers):
    """Test creating a short link with invalid URL"""
    response = await client.post(
        "/links/shorten",
        json={
            "original_url": "invalid-url"
        },
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "invalid url" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_create_short_link_invalid_custom_alias(client: AsyncClient, auth_headers):
    """Test creating a short link with invalid custom alias"""
    response = await client.post(
        "/links/shorten",
        json={
            "original_url": "https://example.com/test",
            "custom_alias": "a"  # Too short
        },
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "invalid custom alias" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_get_link_info(client: AsyncClient, auth_headers):
    """Test getting link information"""
    # First create a link
    create_response = await client.post(
        "/links/shorten",
        json={
            "original_url": "https://example.com/getinfo"
        },
        headers=auth_headers
    )
    
    short_code = create_response.json()["short_code"]
    
    # Get link info
    response = await client.get(f"/links/{short_code}", headers=auth_headers)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["short_code"] == short_code
    assert data["original_url"] == "https://example.com/getinfo"
    assert "created_at" in data
    assert "access_count" in data

@pytest.mark.asyncio
async def test_get_nonexistent_link(client: AsyncClient, auth_headers):
    """Test getting a nonexistent link"""
    response = await client.get("/links/nonexistentcode", headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_update_link(client: AsyncClient, auth_headers):
    """Test updating a link"""
    # First create a link
    create_response = await client.post(
        "/links/shorten",
        json={
            "original_url": "https://example.com/update"
        },
        headers=auth_headers
    )
    
    short_code = create_response.json()["short_code"]
    
    # Update just the URL
    response = await client.put(
        f"/links/{short_code}",
        json={
            "original_url": "https://example.com/updated"
        },
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["original_url"] == "https://example.com/updated"
    
    # Update just the expiration
    new_expiry = (datetime.now() + timedelta(days=30)).isoformat()
    response = await client.put(
        f"/links/{short_code}",
        json={
            "expires_at": new_expiry
        },
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["expires_at"] is not None
    
    # Update both URL and expiration
    response = await client.put(
        f"/links/{short_code}",
        json={
            "original_url": "https://example.com/updated-again",
            "expires_at": (datetime.now() + timedelta(days=60)).isoformat()
        },
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["original_url"] == "https://example.com/updated-again"
    assert data["expires_at"] is not None

@pytest.mark.asyncio
async def test_update_invalid_url(client: AsyncClient, auth_headers):
    """Test updating a link with invalid URL"""
    # First create a link
    create_response = await client.post(
        "/links/shorten",
        json={
            "original_url": "https://example.com/valid"
        },
        headers=auth_headers
    )
    
    short_code = create_response.json()["short_code"]
    
    # Update with invalid URL
    response = await client.put(
        f"/links/{short_code}",
        json={
            "original_url": "invalid-url"
        },
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.asyncio
async def test_update_nonexistent_link(client: AsyncClient, auth_headers):
    """Test updating a nonexistent link"""
    response = await client.put(
        "/links/nonexistentcode",
        json={
            "original_url": "https://example.com/new"
        },
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_delete_link(client: AsyncClient, auth_headers):
    """Test deleting a link"""
    # First create a link
    create_response = await client.post(
        "/links/shorten",
        json={
            "original_url": "https://example.com/delete"
        },
        headers=auth_headers
    )
    
    short_code = create_response.json()["short_code"]
    
    # Delete the link
    response = await client.delete(f"/links/{short_code}", headers=auth_headers)
    
    assert response.status_code == status.HTTP_200_OK
    assert "deleted successfully" in response.json()["detail"].lower()
    
    # Verify link is deleted
    get_response = await client.get(f"/links/{short_code}", headers=auth_headers)
    assert get_response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_delete_nonexistent_link(client: AsyncClient, auth_headers):
    """Test deleting a nonexistent link"""
    response = await client.delete("/links/nonexistentcode", headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_get_link_stats(client: AsyncClient, auth_headers):
    """Test getting link statistics"""
    # First create a link
    create_response = await client.post(
        "/links/shorten",
        json={
            "original_url": "https://example.com/stats"
        },
        headers=auth_headers
    )
    
    short_code = create_response.json()["short_code"]
    
    # Get initial stats
    response = await client.get(f"/links/{short_code}/stats", headers=auth_headers)
    
    assert response.status_code == status.HTTP_200_OK
    initial_data = response.json()
    assert initial_data["short_code"] == short_code
    assert initial_data["original_url"] == "https://example.com/stats"
    assert initial_data["access_count"] == 0
    
    # Access the link to increment stats
    await client.get(f"/{short_code}", follow_redirects=False)
    
    # Get updated stats
    response = await client.get(f"/links/{short_code}/stats", headers=auth_headers)
    
    assert response.status_code == status.HTTP_200_OK
    updated_data = response.json()
    assert updated_data["access_count"] > 0
    assert updated_data["last_accessed_at"] is not None

@pytest.mark.asyncio
async def test_search_links(client: AsyncClient, auth_headers):
    """Test searching for links by original URL"""
    # Create multiple links with similar URLs
    search_term = f"searchtest-{uuid.uuid4().hex[:8]}"  # Use unique search term
    
    urls = [
        f"https://example.com/{search_term}/page1",
        f"https://example.com/{search_term}/page2",
        f"https://different.com/{search_term}"
    ]
    
    # Create links
    for url in urls:
        await client.post(
            "/links/shorten",
            json={"original_url": url},
            headers=auth_headers
        )
    
    # Search with exact match
    response = await client.get(
        "/links/search",
        params={"original_url": urls[0]},
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "links" in data
    assert len(data["links"]) >= 1
    assert any(link["original_url"] == urls[0] for link in data["links"])
    
    # Search with partial match
    response = await client.get(
        "/links/search",
        params={"original_url": search_term},
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "links" in data
    assert len(data["links"]) >= 3  # Should find all three links
    
    # Search with no matches
    response = await client.get(
        "/links/search",
        params={"original_url": "nonexistenturl12345"},
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "links" in data
    assert len(data["links"]) == 0