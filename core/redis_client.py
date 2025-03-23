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
    redis_client = await aioredis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True
    )
    return redis_client

async def close_redis_pool():
    """
    Close Redis connection pool.
    Called during application shutdown.
    """
    if redis_client:
        await redis_client.close()

async def get_redis():
    """
    Get Redis client.
    Use as a dependency in FastAPI endpoints.
    """
    return redis_client

# Cache key prefixes
LINK_PREFIX = "link:"
STATS_PREFIX = "stats:"
AUTH_PREFIX = "auth:"

# Helper functions for common Redis operations
async def cache_link(short_code: str, original_url: str, expires_at=None):
    """Cache a short code to original URL mapping"""
    expire_seconds = None
    if expires_at:
        from datetime import datetime
        delta = expires_at - datetime.now()
        expire_seconds = int(delta.total_seconds())
    
    await redis_client.set(f"{LINK_PREFIX}{short_code}", original_url, ex=expire_seconds)

async def get_cached_link(short_code: str):
    """Get cached original URL for a short code"""
    return await redis_client.get(f"{LINK_PREFIX}{short_code}")

async def delete_cached_link(short_code: str):
    """Delete cached short code"""
    await redis_client.delete(f"{LINK_PREFIX}{short_code}")
    await redis_client.delete(f"{STATS_PREFIX}{short_code}")

async def cache_link_stats(short_code: str, stats_data: dict, ttl_seconds=3600):
    """Cache link statistics data"""
    await redis_client.setex(
        f"{STATS_PREFIX}{short_code}",
        ttl_seconds,
        str(stats_data)
    )

async def get_cached_link_stats(short_code: str):
    """Get cached link statistics"""
    stats_str = await redis_client.get(f"{STATS_PREFIX}{short_code}")
    if stats_str:
        import json
        return json.loads(stats_str.replace("'", "\""))
    return None

async def increment_link_access(short_code: str):
    """Increment link access count in cache"""
    # We'll implement a temporary counter that will be periodically synced to the database
    await redis_client.incr(f"{STATS_PREFIX}{short_code}:count")