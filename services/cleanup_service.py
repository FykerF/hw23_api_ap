import asyncio
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session
from core.config import settings
from core.database import SessionLocal
from services.link_services import cleanup_expired_links, cleanup_unused_links

# Global cleanup task
cleanup_task: Optional[asyncio.Task] = None

async def cleanup_job():
    """
    Periodic job to clean up expired and unused links
    """
    while True:
        try:
            # Create database session
            db = SessionLocal()
            
            # Log cleanup start
            print(f"[{datetime.now()}] Starting link cleanup job")
            
            # Clean up expired links
            expired_count = await cleanup_expired_links(db)
            print(f"[{datetime.now()}] Cleaned up {expired_count} expired links")
            
            # Clean up unused links if enabled
            if settings.CLEANUP_UNUSED_LINKS_DAYS > 0:
                unused_count = await cleanup_unused_links(db, settings.CLEANUP_UNUSED_LINKS_DAYS)
                print(f"[{datetime.now()}] Cleaned up {unused_count} unused links")
                
        except Exception as e:
            print(f"[{datetime.now()}] Error in cleanup job: {str(e)}")
        finally:
            # Close database session
            db.close()
            
        # Sleep until next cleanup interval
        await asyncio.sleep(settings.CLEANUP_JOB_INTERVAL_HOURS * 3600)

async def start_cleanup_scheduler():
    """
    Start the background cleanup task
    """
    global cleanup_task
    
    # Cancel any existing task
    if cleanup_task:
        cleanup_task.cancel()
        
    # Start new task
    cleanup_task = asyncio.create_task(cleanup_job())
    
async def stop_cleanup_scheduler():
    """
    Stop the background cleanup task
    """
    global cleanup_task
    
    if cleanup_task:
        cleanup_task.cancel()
        cleanup_task = None