import pytest
from unittest.mock import MagicMock, patch
import re
from services.shortcode_generator import (
    generate_short_code, 
    is_custom_alias_available, 
    validate_custom_alias
)

class TestShortcodeGenerator:
    """Unit tests for shortcode generator functions"""
    
    def test_generate_short_code(self):
        """Test that generate_short_code produces a valid shortcode"""
        # Mock the database session and query
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_first = MagicMock(return_value=None)  # No existing link found
        
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = mock_first.return_value
        
        # Mock settings for consistent testing
        with patch('services.shortcode_generator.settings') as mock_settings:
            mock_settings.SHORTCODE_LENGTH = 6
            
            # Generate shortcode
            shortcode = generate_short_code(mock_db)
            
            # Verify shortcode format
            assert isinstance(shortcode, str)
            assert len(shortcode) == 6
            assert re.match(r'^[a-zA-Z0-9]+$', shortcode)  # Alphanumeric chars only
            
            # Verify database was queried
            mock_db.query.assert_called_once()
    
    def test_generate_short_code_retry_on_collision(self):
        """Test that generate_short_code retries if collision detected"""
        # Set up mock to return existing link on first call, None on second call
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_filter = MagicMock()
        
        # Mock the existing link result for first attempt
        mock_link = MagicMock()
        # Return existing link first, then None to simulate successful second attempt
        mock_filter.first.side_effect = [mock_link, None]
        
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        
        # Mock settings for consistent testing
        with patch('services.shortcode_generator.settings') as mock_settings:
            mock_settings.SHORTCODE_LENGTH = 6
            
            # Generate shortcode
            shortcode = generate_short_code(mock_db)
            
            # Verify database was queried twice (collision, then success)
            assert mock_filter.first.call_count == 2
            assert shortcode is not None
    
    @pytest.mark.parametrize("alias,expected", [
        ("mylink", True),
        ("test123", True),
        ("a-b-c", True),
        ("with_underscore", True),
        ("ab", False),           # Too short
        ("a" * 21, False),       # Too long
        ("my link", False),      # Contains space
        ("my.link", False),      # Contains invalid char
        ("admin", False),        # Reserved word
        ("api", False),          # Reserved word
        ("links", False),        # Reserved word
    ])
    def test_validate_custom_alias(self, alias, expected):
        """Test validation of custom aliases"""
        assert validate_custom_alias(alias) == expected
    
    def test_is_custom_alias_available(self):
        """Test checking availability of custom aliases"""
        # Mock the database session
        mock_db = MagicMock()
        
        # Mock for an available alias (no existing link)
        mock_db.query().filter().first.return_value = None
        assert is_custom_alias_available(mock_db, "available") is True
        
        # Mock for an unavailable alias (existing link found)
        mock_link = MagicMock()
        mock_db.query().filter().first.return_value = mock_link
        assert is_custom_alias_available(mock_db, "unavailable") is False