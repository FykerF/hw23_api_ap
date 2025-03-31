import pytest
from utils.validators import validate_url, validate_email, validate_username, validate_password

class TestValidators:
    """Unit tests for validator functions in utils/validators.py"""
    
    @pytest.mark.parametrize("url,expected", [
        ("https://example.com", True),
        ("http://example.com/path?query=123", True),
        ("https://subdomain.example.co.uk/path", True),
        ("ftp://example.com", True),
        ("example.com", False),  # Missing scheme
        ("http://", False),      # Missing domain
        ("invalid-url", False),
        ("", False),
    ])
    def test_validate_url(self, url, expected):
        """Test URL validation with various inputs"""
        assert validate_url(url) == expected
    
    @pytest.mark.parametrize("email,expected", [
        ("user@example.com", True),
        ("user.name+tag@example.co.uk", True),
        ("user@sub.domain.com", True),
        ("user@localhost", True),
        ("user@127.0.0.1", True),
        ("@example.com", False),     # Missing username
        ("user@", False),            # Missing domain
        ("user@.com", False),        # Invalid domain
        ("user example.com", False), # Contains space
        ("", False),
    ])
    def test_validate_email(self, email, expected):
        """Test email validation with various inputs"""
        assert validate_email(email) == expected
    
    @pytest.mark.parametrize("username,expected", [
        ("user123", True),
        ("user_name", True),
        ("user-name", True),
        ("a12", True),               # Minimum length (3)
        ("abcdefghij1234567890", True), # Maximum length (20)
        ("ab", False),               # Too short
        ("abcdefghij12345678901", False), # Too long
        ("user name", False),        # Contains space
        ("user@name", False),        # Contains invalid chars
        ("", False),
    ])
    def test_validate_username(self, username, expected):
        """Test username validation with various inputs"""
        assert validate_username(username) == expected
    
    @pytest.mark.parametrize("password,expected", [
        ("password123", True),
        ("P@ssw0rd", True),
        ("12345678", True),          # Minimum length (8)
        ("1234567", False),          # Too short
        ("", False),
    ])
    def test_validate_password(self, password, expected):
        """Test password validation with various inputs"""
        assert validate_password(password) == expected