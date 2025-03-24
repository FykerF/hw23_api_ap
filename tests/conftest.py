import asyncio
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os
import sys

# Add parent directory to path to find modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from core.database import get_db, Base
from core.redis_client import init_redis_pool, close_redis_pool
from api.controllers.auth_controller import create_access_token

# Use test database instead of production database
TEST_DATABASE_URL = "postgresql://postgres:postgres@postgres:5432/urlshortener_test"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_db():
    """Initialize test database for testing."""
    from sqlalchemy import create_engine
    
    # Create test database
    engine = create_engine(TEST_DATABASE_URL)
    
    # Create tables
    Base.metadata.create_all(engine)
    
    yield
    
    # Drop tables after tests
    Base.metadata.drop_all(engine)

@pytest.fixture(scope="function")
async def db_session(test_db):
    """Create a fresh database session for each test."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    engine = create_engine(TEST_DATABASE_URL)
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    session = TestSessionLocal()
    
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
async def override_get_db(db_session):
    """Override get_db dependency to use test database."""
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    return _override_get_db

@pytest.fixture
async def client(override_get_db):
    """Create test client with overridden dependencies."""
    # Override get_db dependency
    app.dependency_overrides[get_db] = override_get_db
    
    # Initialize Redis for testing
    await init_redis_pool()
    
    # Create client with async with statement
    client = AsyncClient(app=app, base_url="http://test")
    yield client  # Change this line from 'async with' to just 'yield'
    
    # Close Redis connection
    await close_redis_pool()
    
    # Remove dependency override
    app.dependency_overrides = {}

@pytest.fixture
async def auth_headers(client, override_get_db):
    """Create authentication headers for tests."""
    # Create test user
    from api.controllers.auth_controller import create_user
    
    db = next(override_get_db())
    
    # Check if test user already exists
    from api.controllers.auth_controller import get_user_by_email
    
    test_user = get_user_by_email(db, "test@example.com")
    
    if not test_user:
        test_user = create_user(
            db=db,
            username="testuser",
            email="test@example.com",
            password="testpassword"
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": test_user.id})
    
    return {"Authorization": f"Bearer {access_token}"}