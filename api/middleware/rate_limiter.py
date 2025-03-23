from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from core.config import settings
from core.redis_client import redis_client
import time

class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Middleware for rate limiting requests based on IP address
    """
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for certain paths (e.g., healthchecks)
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
            
        # Get client IP address
        client_ip = request.client.host
        
        # Create Redis key for this IP
        key = f"rate_limit:{client_ip}"
        
        # Get current count from Redis
        count = await redis_client.get(key)
        
        # If no count exists, initialize it
        if count is None:
            await redis_client.setex(key, 60, "1")
        else:
            # If count exists, increment it
            count = int(count)
            
            # If count exceeds limit, return 429 Too Many Requests
            if count >= settings.RATE_LIMIT_PER_MINUTE:
                # Get TTL of key to inform client when they can try again
                ttl = await redis_client.ttl(key)
                
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Try again in {ttl} seconds.",
                    headers={"Retry-After": str(ttl)}
                )
            
            # Otherwise, increment count
            await redis_client.incr(key)
            
            # Ensure the key expires after 60 seconds (if not already set)
            ttl = await redis_client.ttl(key)
            if ttl == -1:
                await redis_client.expire(key, 60)
        
        # Proceed with request
        response = await call_next(request)
        
        return response