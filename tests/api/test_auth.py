import pytest
from httpx import AsyncClient
from fastapi import status
import uuid

@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    """Test user registration"""
    # Generate unique username and email for test
    unique_id = uuid.uuid4().hex[:8]
    username = f"testuser_{unique_id}"
    email = f"test_{unique_id}@example.com"
    
    response = await client.post(
        "/auth/register",
        json={
            "username": username,
            "email": email,
            "password": "securepassword123"
        }
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["username"] == username
    assert data["email"] == email
    assert "id" in data

@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    """Test registration with duplicate email"""
    # First registration
    unique_id = uuid.uuid4().hex[:8]
    username1 = f"testuser1_{unique_id}"
    email = f"duplicate_{unique_id}@example.com"
    
    await client.post(
        "/auth/register",
        json={
            "username": username1,
            "email": email,
            "password": "securepassword123"
        }
    )
    
    # Second registration with same email
    username2 = f"testuser2_{unique_id}"
    response = await client.post(
        "/auth/register",
        json={
            "username": username2,
            "email": email,  # Same email
            "password": "securepassword123"
        }
    )
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "already registered" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_register_duplicate_username(client: AsyncClient):
    """Test registration with duplicate username"""
    # First registration
    unique_id = uuid.uuid4().hex[:8]
    username = f"testuser_{unique_id}"
    email1 = f"test1_{unique_id}@example.com"
    
    await client.post(
        "/auth/register",
        json={
            "username": username,
            "email": email1,
            "password": "securepassword123"
        }
    )
    
    # Second registration with same username
    email2 = f"test2_{unique_id}@example.com"
    response = await client.post(
        "/auth/register",
        json={
            "username": username,  # Same username
            "email": email2,
            "password": "securepassword123"
        }
    )
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "already taken" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_register_invalid_data(client: AsyncClient):
    """Test registration with invalid data"""
    # Test with short username
    response = await client.post(
        "/auth/register",
        json={
            "username": "ab",  # Too short
            "email": "test@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    # Test with invalid email
    response = await client.post(
        "/auth/register",
        json={
            "username": "validuser",
            "email": "invalid-email",  # Invalid format
            "password": "password123"
        }
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    # Test with short password
    response = await client.post(
        "/auth/register",
        json={
            "username": "validuser",
            "email": "test@example.com",
            "password": "short"  # Too short
        }
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """Test successful login"""
    # Register a user first
    unique_id = uuid.uuid4().hex[:8]
    username = f"logintest_{unique_id}"
    email = f"login_{unique_id}@example.com"
    password = "securepassword123"
    
    await client.post(
        "/auth/register",
        json={
            "username": username,
            "email": email,
            "password": password
        }
    )
    
    # Login with email/password
    response = await client.post(
        "/auth/login",
        data={
            "username": email,  # Login uses email
            "password": password
        }
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 0

@pytest.mark.asyncio
async def test_login_wrong_credentials(client: AsyncClient):
    """Test login with wrong credentials"""
    # Login with non-existent user
    response = await client.post(
        "/auth/login",
        data={
            "username": "nonexistent@example.com",
            "password": "wrongpassword"
        }
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    # Register a user
    unique_id = uuid.uuid4().hex[:8]
    username = f"wrongpw_{unique_id}"
    email = f"wrongpw_{unique_id}@example.com"
    password = "securepassword123"
    
    await client.post(
        "/auth/register",
        json={
            "username": username,
            "email": email,
            "password": password
        }
    )
    
    # Login with correct email but wrong password
    response = await client.post(
        "/auth/login",
        data={
            "username": email,
            "password": "wrongpassword"
        }
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_get_current_user(client: AsyncClient, auth_headers):
    """Test getting current user information"""
    response = await client.get("/auth/me", headers=auth_headers)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "id" in data
    assert "username" in data
    assert "email" in data

@pytest.mark.asyncio
async def test_get_current_user_no_token(client: AsyncClient):
    """Test getting user info without auth token"""
    response = await client.get("/auth/me")
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
@pytest.mark.asyncio
async def test_get_current_user_invalid_token(client: AsyncClient):
    """Test getting user info with invalid auth token"""
    headers = {"Authorization": "Bearer invalid_token"}
    response = await client.get("/auth/me", headers=headers)
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED