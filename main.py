import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from api.routes import auth, links
from api.middleware.rate_limiter import RateLimiterMiddleware
from core.config import settings
from core.database import create_tables

app = FastAPI(
    title=settings.APP_NAME,
    description="API service for shortening URLs, with analytics and management features",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting middleware
app.add_middleware(RateLimiterMiddleware)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(links.router, prefix="/links", tags=["Link Management"])

# Redirect endpoint
@app.get("/{short_code}", include_in_schema=False)
async def redirect_to_original_url(short_code: str, request: Request):
    from api.controllers.link_controller import get_original_url
    original_url = await get_original_url(short_code, request.client.host)
    return RedirectResponse(url=original_url)

@app.on_event("startup")
async def startup_event():
    # Create database tables if they don't exist
    create_tables()
    
    # Connect to Redis
    from core.redis_client import init_redis_pool
    await init_redis_pool()
    
    # Start cleanup scheduled job
    from services.cleanup_service import start_cleanup_scheduler
    await start_cleanup_scheduler()

@app.on_event("shutdown")
async def shutdown_event():
    # Close Redis connection
    from core.redis_client import close_redis_pool
    await close_redis_pool()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )