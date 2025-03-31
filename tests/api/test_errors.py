import pytest
from httpx import AsyncClient
from fastapi import status
import uuid

@pytest.mark.asyncio
async def test_404_nonexistent_endpoint(client: AsyncClient):
    """Test 404 response for nonexistent endpoint"""
    response = await client.get("/nonexistent-endpoint")
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_405_method_not_allowed(client: AsyncClient):
    """Test 405 response for methods not allowed"""
    # PUT not allowed on /links/shorten
    response = await client.put("/links/shorten", json={"original_url": "https://example.com"})
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    
    # DELETE not allowed on /links/search
    response = await client.delete("/links/search")
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

@pytest.mark.asyncio
async def test_422_validation_error(client: AsyncClient):
    """Test 422 response for validation errors"""
    # Missing required field
    response = await client.post("/links/shorten", json={})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    # Invalid expiration date format
    response = await client.post(
        "/links/shorten", 
        json={
            "original_url": "https://example.com",
            "expires_at": "invalid-date"
        }
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

@pytest.mark.asyncio
async def test_401_unauthorized(client: AsyncClient):
    """Test 401 response for unauthorized access"""
    # Create a link that we'll try to update without auth
    create_response = await client.post(
        "/links/shorten",
        json={"original_url": "https://example.com/authtest"}
    )
    
    assert create_response.status_code == status.HTTP_200_OK
    short_code = create_response.json()["short_code"]
    
    # Try to update without auth
    response = await client.put(
        f"/links/{short_code}",
        json={"original_url": "https://example.com/updated"}
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    # Try to access protected endpoint without auth
    response = await client.get("/auth/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    # Invalid token
    headers = {"Authorization": "Bearer invalid_token_here"}
    response = await client.get("/auth/me", headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_403_forbidden(client: AsyncClient, auth_headers):
    """Test 403 response for forbidden access"""
    # Create user A with auth token
    first_auth_headers = auth_headers
    
    # Create a link with user A
    create_response = await client.post(
        "/links/shorten",
        json={"original_url": "https://example.com/userA-link"},
        headers=first_auth_headers
    )
    
    assert create_response.status_code == status.HTTP_200_OK
    short_code = create_response.json()["short_code"]
    
    # Create user B with different auth token
    register_response = await client.post(
        "/auth/register",
        json={
            "username": f"userB_{uuid.uuid4().hex[:8]}",
            "email": f"userB_{uuid.uuid4().hex[:8]}@example.com",
            "password": "password123"
        }
    )
    assert register_response.status_code == status.HTTP_200_OK
    
    login_response = await client.post(
        "/auth/login",
        data={
            "username": register_response.json()["email"],
            "password": "password123"
        }
    )
    assert login_response.status_code == status.HTTP_200_OK
    
    second_auth_headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}
    
    # Try to update user A's link with user B's token
    response = await client.put(
        f"/links/{short_code}",
        json={"original_url": "https://example.com/updated-by-userB"},
        headers=second_auth_headers
    )
    
    # Should be forbidden
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "not authorized" in response.json()["detail"].lower()
    
    # Try to delete user A's link with user B's token
    response = await client.delete(
        f"/links/{short_code}",
        headers=second_auth_headers
    )
    
    # Should be forbidden
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "not authorized" in response.json()["detail"].lower()