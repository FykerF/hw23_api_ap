import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timedelta, timezone
import json

from core.redis_client import (
    cache_link,
    get_cached_link,
    delete_cached_link,
    cache_link_stats,
    get_cached_link_stats,
    increment_link_access,
    LINK_PREFIX,
    STATS_PREFIX
)

class TestRedisClient:
    """Unit tests for Redis caching functions"""
    
    @pytest.mark.asyncio
    @patch('core.redis_client.get_redis')
    async def test_cache_link(self, mock_get_redis):
        """Test caching a link"""
        # Create mock Redis client
        mock_redis = AsyncMock()
        mock_get_redis.return_value = mock_redis
        
        # Test basic caching without expiration
        short_code = "testcode"
        original_url = "https://example.com/test"
        
        await cache_link(short_code, original_url)
        
        # Verify Redis set was called correctly
        mock_redis.set.assert_called_once_with(f"{LINK_PREFIX}{short_code}", original_url, ex=None)
        
        # Reset mocks
        mock_redis.reset_mock()
        
        # Test with expiration
        expires_at = datetime.now(timezone.utc) + timedelta(days=1)
        
        await cache_link(short_code, original_url, expires_at)
        
        # Verify Redis set was called with expiration
        mock_redis.set.assert_called_once()
        args, kwargs = mock_redis.set.call_args
        assert args[0] == f"{LINK_PREFIX}{short_code}"
        assert args[1] == original_url
        assert kwargs.get('ex') is not None
        assert kwargs.get('ex') > 0
        
        # Test with expired link
        mock_redis.reset_mock()
        expires_at = datetime.now(timezone.utc) - timedelta(days=1)  # Already expired
        
        await cache_link(short_code, original_url, expires_at)
        
        # Verify Redis set was not called for expired link
        mock_redis.set.assert_not_called()
    
    @pytest.mark.asyncio
    @patch('core.redis_client.get_redis')
    async def test_get_cached_link(self, mock_get_redis):
        """Test retrieving a cached link"""
        # Create mock Redis client
        mock_redis = AsyncMock()
        mock_get_redis.return_value = mock_redis
        
        # Test when link exists in cache
        short_code = "testcode"
        original_url = "https://example.com/test"
        mock_redis.get.return_value = original_url
        
        result = await get_cached_link(short_code)
        
        # Verify Redis get was called correctly
        mock_redis.get.assert_called_once_with(f"{LINK_PREFIX}{short_code}")
        assert result == original_url
        
        # Test when link does not exist in cache
        mock_redis.reset_mock()
        mock_redis.get.return_value = None
        
        result = await get_cached_link(short_code)
        
        mock_redis.get.assert_called_once_with(f"{LINK_PREFIX}{short_code}")
        assert result is None
        
        # Test when Redis is not available
        mock_get_redis.return_value = None
        
        result = await get_cached_link(short_code)
        
        assert result is None
    
    @pytest.mark.asyncio
    @patch('core.redis_client.get_redis')
    async def test_delete_cached_link(self, mock_get_redis):
        """Test deleting a cached link"""
        # Create mock Redis client
        mock_redis = AsyncMock()
        mock_get_redis.return_value = mock_redis
        
        short_code = "testcode"
        
        await delete_cached_link(short_code)
        
        # Verify Redis delete was called correctly for both link and stats
        assert mock_redis.delete.call_count == 2
        mock_redis.delete.assert_any_call(f"{LINK_PREFIX}{short_code}")
        mock_redis.delete.assert_any_call(f"{STATS_PREFIX}{short_code}")
        
        # Test when Redis is not available
        mock_redis.reset_mock()
        mock_get_redis.return_value = None
        
        await delete_cached_link(short_code)
        
        # Verify no errors and no calls
        mock_redis.delete.assert_not_called()
    
    @pytest.mark.asyncio
    @patch('core.redis_client.get_redis')
    async def test_cache_link_stats(self, mock_get_redis):
        """Test caching link statistics"""
        # Create mock Redis client
        mock_redis = AsyncMock()
        mock_get_redis.return_value = mock_redis
        
        short_code = "testcode"
        stats_data = {
            "short_code": short_code,
            "original_url": "https://example.com/test",
            "access_count": 42,
            "created_at": "2023-01-01T12:00:00",
            "last_accessed_at": "2023-01-15T08:30:00"
        }
        
        await cache_link_stats(short_code, stats_data)
        
        # Verify Redis setex was called correctly
        mock_redis.setex.assert_called_once()
        args, _ = mock_redis.setex.call_args
        assert args[0] == f"{STATS_PREFIX}{short_code}"
        assert isinstance(args[1], int)  # TTL
        assert isinstance(args[2], str)  # Stats data as string
        
        # Test when Redis is not available
        mock_redis.reset_mock()
        mock_get_redis.return_value = None
        
        await cache_link_stats(short_code, stats_data)
        
        # Verify no errors and no calls
        mock_redis.setex.assert_not_called()
    
    @pytest.mark.asyncio
    @patch('core.redis_client.get_redis')
    async def test_get_cached_link_stats(self, mock_get_redis):
        """Test retrieving cached link statistics"""
        # Create mock Redis client
        mock_redis = AsyncMock()
        mock_get_redis.return_value = mock_redis
        
        short_code = "testcode"
        stats_data = {
            "short_code": short_code,
            "original_url": "https://example.com/test",
            "access_count": 42,
            "created_at": "2023-01-01T12:00:00",
            "last_accessed_at": "2023-01-15T08:30:00"
        }
        
        # Test when stats exist in cache
        mock_redis.get.return_value = str(stats_data).replace("'", "\"")
        
        result = await get_cached_link_stats(short_code)
        
        # Verify Redis get was called correctly
        mock_redis.get.assert_called_once_with(f"{STATS_PREFIX}{short_code}")
        assert result == stats_data
        
        # Test when stats do not exist in cache
        mock_redis.reset_mock()
        mock_redis.get.return_value = None
        
        result = await get_cached_link_stats(short_code)
        
        mock_redis.get.assert_called_once_with(f"{STATS_PREFIX}{short_code}")
        assert result is None
        
        # Test when Redis is not available
        mock_get_redis.return_value = None
        
        result = await get_cached_link_stats(short_code)
        
        assert result is None
    
    @pytest.mark.asyncio
    @patch('core.redis_client.get_redis')
    async def test_increment_link_access(self, mock_get_redis):
        """Test incrementing link access count in cache"""
        # Create mock Redis client
        mock_redis = AsyncMock()
        mock_get_redis.return_value = mock_redis
        
        short_code = "testcode"
        
        await increment_link_access(short_code)
        
        # Verify Redis incr was called correctly
        mock_redis.incr.assert_called_once_with(f"{STATS_PREFIX}{short_code}:count")
        
        # Test when Redis is not available
        mock_redis.reset_mock()
        mock_get_redis.return_value = None
        
        await increment_link_access(short_code)
        
        # Verify no errors and no calls
        mock_redis.incr.assert_not_called()