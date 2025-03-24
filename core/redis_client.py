import aioredis
from core.config import settings

# Global Redis connection
redis_client = None

async def init_redis_pool():
    """
    Initialize Redis connection pool.
    Called during application startup.
    """
    global redis_client
    try:
        redis_client = await aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
        return redis_client
    except Exception as e:
        print(f"Failed to connect to Redis: {str(e)}")
        return None

async def close_redis_pool():
    """
    Close Redis connection pool.
    Called during application shutdown.
    """
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None

async def get_redis():
    """
    Get Redis client.
    Use as a dependency in FastAPI endpoints.
    
    Returns:
        Redis client or None if connection failed
    """
    # If redis_client is None, try to initialize it
    global redis_client
    if redis_client is None:
        redis_client = await init_redis_pool()
    return redis_client

# Cache key prefixes
LINK_PREFIX = "link:"
STATS_PREFIX = "stats:"
AUTH_PREFIX = "auth:"

async def cache_link(short_code: str, original_url: str, expires_at=None):
    """Cache a short code to original URL mapping"""
    redis = await get_redis()
    if not redis:
        return
        
    expire_seconds = None
    if expires_at:
        from datetime import datetime, timezone
        # Make sure both datetimes are timezone-aware
        now = datetime.now(timezone.utc)
        
        # Convert expires_at to timezone-aware if it's not already
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
            
        delta = expires_at - now
        expire_seconds = int(delta.total_seconds())
        if expire_seconds <= 0:
            # Don't cache if already expired
            return
    
    await redis.set(f"{LINK_PREFIX}{short_code}", original_url, ex=expire_seconds)

async def get_cached_link(short_code: str):
    """Get cached original URL for a short code"""
    redis = await get_redis()
    if not redis:
        return None
    return await redis.get(f"{LINK_PREFIX}{short_code}")

async def delete_cached_link(short_code: str):
    """Delete cached short code"""
    redis = await get_redis()
    if not redis:
        return
    await redis.delete(f"{LINK_PREFIX}{short_code}")
    await redis.delete(f"{STATS_PREFIX}{short_code}")

async def cache_link_stats(short_code: str, stats_data: dict, ttl_seconds=3600):
    """Cache link statistics data"""
    redis = await get_redis()
    if not redis:
        return
    await redis.setex(
        f"{STATS_PREFIX}{short_code}",
        ttl_seconds,
        str(stats_data)
    )

async def get_cached_link_stats(short_code: str):
    """Get cached link statistics"""
    redis = await get_redis()
    if not redis:
        return None
    stats_str = await redis.get(f"{STATS_PREFIX}{short_code}")
    if stats_str:
        import json
        return json.loads(stats_str.replace("'", "\""))
    return None

async def increment_link_access(short_code: str):
    """Increment link access count in cache"""
    redis = await get_redis()
    if not redis:
        return
    # We'll implement a temporary counter that will be periodically synced to the database
    await redis.incr(f"{STATS_PREFIX}{short_code}:count")