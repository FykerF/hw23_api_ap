import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import uuid
from fastapi import HTTPException

from api.controllers.auth_controller import (
    verify_password, 
    get_password_hash, 
    get_user_by_email, 
    get_user_by_username, 
    get_user_by_id,
    create_user,
    authenticate_user,
    create_access_token,
    get_current_user
)
from api.models.user import User

class TestAuthController:
    """Unit tests for authentication controller functions"""
    
    def test_password_hash_and_verify(self):
        """Test password hashing and verification"""
        password = "securepassword123"
        hashed = get_password_hash(password)
        
        # Verify the hash is different from the original password
        assert hashed != password
        
        # Verify correct password validates
        assert verify_password(password, hashed) is True
        
        # Verify incorrect password fails
        assert verify_password("wrongpassword", hashed) is False
    
    def test_get_user_by_email(self):
        """Test retrieving a user by email"""
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_user = MagicMock()
        
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_user
        
        result = get_user_by_email(mock_db, "test@example.com")
        
        mock_db.query.assert_called_once()
        assert result == mock_user
    
    def test_get_user_by_username(self):
        """Test retrieving a user by username"""
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_user = MagicMock()
        
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_user
        
        result = get_user_by_username(mock_db, "testuser")
        
        mock_db.query.assert_called_once()
        assert result == mock_user
    
    def test_get_user_by_id(self):
        """Test retrieving a user by ID"""
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_user = MagicMock()
        user_id = str(uuid.uuid4())
        
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_user
        
        result = get_user_by_id(mock_db, user_id)
        
        mock_db.query.assert_called_once()
        assert result == mock_user
    
    @patch('api.controllers.auth_controller.get_password_hash')
    @patch('api.controllers.auth_controller.uuid.uuid4')
    def test_create_user(self, mock_uuid, mock_get_password_hash):
        """Test user creation"""
        mock_db = MagicMock()
        mock_user = MagicMock()
        
        # Mock UUID and password hash
        user_id = "test-uuid-123"
        mock_uuid.return_value = user_id
        mock_get_password_hash.return_value = "hashed_password"
        
        # Mock user data
        username = "testuser"
        email = "test@example.com"
        password = "password123"
        
        # Mock db.add
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()
        
        # Create a user
        result = create_user(mock_db, username, email, password)
        
        # Verify database operations
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
        
        # Get the User object that was passed to db.add
        added_user = mock_db.add.call_args[0][0]
        
        # Verify user properties
        assert added_user.id == user_id
        assert added_user.username == username
        assert added_user.email == email
        assert added_user.password_hash == "hashed_password"
    
    @patch('api.controllers.auth_controller.get_user_by_email')
    @patch('api.controllers.auth_controller.verify_password')
    def test_authenticate_user_success(self, mock_verify_password, mock_get_user_by_email):
        """Test successful user authentication"""
        mock_db = MagicMock()
        mock_user = MagicMock()
        
        # Mock successful authentication
        mock_get_user_by_email.return_value = mock_user
        mock_verify_password.return_value = True
        
        # Authenticate
        result = authenticate_user(mock_db, "test@example.com", "password123")
        
        # Verify result
        assert result == mock_user
        mock_get_user_by_email.assert_called_once_with(mock_db, "test@example.com")
        mock_verify_password.assert_called_once()
    
    @patch('api.controllers.auth_controller.get_user_by_email')
    def test_authenticate_user_no_user(self, mock_get_user_by_email):
        """Test authentication with non-existent user"""
        mock_db = MagicMock()
        
        # Mock user not found
        mock_get_user_by_email.return_value = None
        
        # Authenticate
        result = authenticate_user(mock_db, "nonexistent@example.com", "password123")
        
        # Verify result
        assert result is None
        mock_get_user_by_email.assert_called_once_with(mock_db, "nonexistent@example.com")
    
    @patch('api.controllers.auth_controller.get_user_by_email')
    @patch('api.controllers.auth_controller.verify_password')
    def test_authenticate_user_wrong_password(self, mock_verify_password, mock_get_user_by_email):
        """Test authentication with wrong password"""
        mock_db = MagicMock()
        mock_user = MagicMock()
        
        # Mock user found but wrong password
        mock_get_user_by_email.return_value = mock_user
        mock_verify_password.return_value = False
        
        # Authenticate
        result = authenticate_user(mock_db, "test@example.com", "wrongpassword")
        
        # Verify result
        assert result is None
        mock_get_user_by_email.assert_called_once_with(mock_db, "test@example.com")
        mock_verify_password.assert_called_once()
    
    @patch('api.controllers.auth_controller.jwt.encode')
    def test_create_access_token(self, mock_jwt_encode):
        """Test JWT access token creation"""
        # Mock JWT encode
        mock_jwt_encode.return_value = "encoded_jwt_token"
        
        # Create token data
        data = {"sub": "user_id"}
        expires_delta = timedelta(minutes=30)
        
        # Create token
        token = create_access_token(data, expires_delta)
        
        # Verify result
        assert token == "encoded_jwt_token"
        mock_jwt_encode.assert_called_once()
        
        # Extract the data that was passed to jwt.encode
        encoded_data = mock_jwt_encode.call_args[0][0]
        
        # Verify data properties
        assert encoded_data["sub"] == "user_id"
        assert "exp" in encoded_data
    
    @patch('api.controllers.auth_controller.jwt.decode')
    @patch('api.controllers.auth_controller.get_user_by_id')
    @patch('api.controllers.auth_controller.get_redis')
    async def test_get_current_user_success(self, mock_get_redis, mock_get_user_by_id, mock_jwt_decode):
        """Test successful current user retrieval from token"""
        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_redis = MagicMock()
        
        # Mock Redis exist check (token not blacklisted)
        mock_redis.exists.return_value = False
        mock_get_redis.return_value = mock_redis
        
        # Mock JWT decode
        mock_jwt_decode.return_value = {"sub": "user_id"}
        
        # Mock user retrieval
        mock_get_user_by_id.return_value = mock_user
        
        # Get current user
        result = await get_current_user("valid_token", mock_db)
        
        # Verify result
        assert result == mock_user
        mock_jwt_decode.assert_called_once()
        mock_get_user_by_id.assert_called_once_with(mock_db, "user_id")
    
    @patch('api.controllers.auth_controller.jwt.decode')
    async def test_get_current_user_invalid_token(self, mock_jwt_decode):
        """Test invalid token handling"""
        mock_db = MagicMock()
        
        # Mock JWT decode failure
        mock_jwt_decode.side_effect = Exception("Invalid token")
        
        # Get current user
        with pytest.raises(HTTPException) as exc:
            await get_current_user("invalid_token", mock_db)
        
        # Verify exception
        assert exc.value.status_code == 401
        mock_jwt_decode.assert_called_once()