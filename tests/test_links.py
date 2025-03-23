import pytest
from httpx import AsyncClient
from fastapi import status
from datetime import datetime, timedelta
import json

from main import app
from core.database import get_db, SessionLocal

# Test fixtures will be imported from conftest.py

@pytest.mark.asyncio
async def test_create_short_link(client: AsyncClient, auth_headers):
    # Test creating a short link with authentication
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
    short_code = data["short_code"]
    return short_code

@pytest.mark.asyncio
async def test_create_short_link_anonymous(client: AsyncClient):
    # Test creating a short link without authentication
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
async def test_create_short_link_with_custom_alias(client: AsyncClient):
    # Test creating a short link with custom alias
    response = await client.post(
        "/links/shorten",
        json={
            "original_url": "https://example.com/custom",
            "custom_alias": "mytest"
        }
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["short_code"] == "mytest"
    assert data["original_url"] == "https://example.com/custom"

@pytest.mark.asyncio
async def test_create_short_link_with_invalid_url(client: AsyncClient):
    # Test creating a short link with invalid URL
    response = await client.post(
        "/links/shorten",
        json={
            "original_url": "invalid-url"
        }
    )
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.asyncio
async def test_create_short_link_with_duplicate_alias(client: AsyncClient):
    # First create a link with custom alias
    await client.post(
        "/links/shorten",
        json={
            "original_url": "https://example.com/first",
            "custom_alias": "duplicate"
        }
    )
    
    # Try to create another link with the same alias
    response = await client.post(
        "/links/shorten",
        json={
            "original_url": "https://example.com/second",
            "custom_alias": "duplicate"
        }
    )
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.asyncio
async def test_get_link_info(client: AsyncClient, auth_headers):
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

@pytest.mark.asyncio
async def test_update_link(client: AsyncClient, auth_headers):
    # First create a link
    create_response = await client.post(
        "/links/shorten",
        json={
            "original_url": "https://example.com/update"
        },
        headers=auth_headers
    )
    
    short_code = create_response.json()["short_code"]
    
    # Update link
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

@pytest.mark.asyncio
async def test_delete_link(client: AsyncClient, auth_headers):
    # First create a link
    create_response = await client.post(
        "/links/shorten",
        json={
            "original_url": "https://example.com/delete"
        },
        headers=auth_headers
    )
    
    short_code = create_response.json()["short_code"]
    
    # Delete link
    response = await client.delete(f"/links/{short_code}", headers=auth_headers)
    
    assert response.status_code == status.HTTP_200_OK
    
    # Verify link is deleted
    get_response = await client.get(f"/links/{short_code}", headers=auth_headers)
    assert get_response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_get_link_stats(client: AsyncClient, auth_headers):
    # First create a link
    create_response = await client.post(
        "/links/shorten",
        json={
            "original_url": "https://example.com/stats"
        },
        headers=auth_headers
    )
    
    short_code = create_response.json()["short_code"]
    
    # Get link stats
    response = await client.get(f"/links/{short_code}/stats", headers=auth_headers)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["short_code"] == short_code
    assert data["original_url"] == "https://example.com/stats"
    assert "access_count" in data
    assert "created_at" in data

@pytest.mark.asyncio
async def test_search_links(client: AsyncClient, auth_headers):
    # First create a link
    await client.post(
        "/links/shorten",
        json={
            "original_url": "https://example.com/searchtest"
        },
        headers=auth_headers
    )
    
    # Search links
    response = await client.get(
        "/links/search",
        params={"original_url": "example.com/searchtest"},
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "links" in data
    assert len(data["links"]) > 0
    assert "example.com/searchtest" in data["links"][0]["original_url"]

@pytest.mark.asyncio
async def test_redirect(client: AsyncClient):
    # First create a link
    create_response = await client.post(
        "/links/shorten",
        json={
            "original_url": "https://example.com/redirect"
        }
    )
    
    short_code = create_response.json()["short_code"]
    
    # Test redirect
    response = await client.get(f"/{short_code}", follow_redirects=False)
    
    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert response.headers["location"] == "https://example.com/redirect"