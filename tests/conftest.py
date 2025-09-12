"""
Pytest configuration and fixtures for Digital Krishi Officer API tests.
"""

import pytest
import asyncio
import asyncpg
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.database import Base


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_db():
    """Create a test database."""
    # Create test database URL
    test_db_url = settings.database_url.replace("/krishi_officer", "/test_krishi_officer")
    
    # Connect to postgres to create test database
    conn = await asyncpg.connect(
        user="n8n",
        password="n8npassword", 
        host="localhost",
        database="postgres"
    )
    
    try:
        await conn.execute("DROP DATABASE IF EXISTS test_krishi_officer")
        await conn.execute("CREATE DATABASE test_krishi_officer")
    finally:
        await conn.close()
    
    # Create test engine
    engine = create_async_engine(test_db_url, echo=False)
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield test_db_url
    
    # Cleanup
    await engine.dispose()
    
    # Drop test database
    conn = await asyncpg.connect(
        user="n8n",
        password="n8npassword",
        host="localhost", 
        database="postgres"
    )
    
    try:
        await conn.execute("DROP DATABASE test_krishi_officer")
    finally:
        await conn.close()


@pytest.fixture
async def db_session(test_db) -> AsyncGenerator[AsyncSession, None]:
    """Create a database session for testing."""
    engine = create_async_engine(test_db, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        yield session
    
    await engine.dispose()


@pytest.fixture
def test_user_data():
    """Test user data fixture."""
    return {
        "email": "testuser@example.com",
        "full_name": "Test User",
        "password": "testpassword123",
        "phone_number": "+1234567890",
        "location": "Test Location",
        "latitude": 10.0,
        "longitude": 76.0
    }


@pytest.fixture
def test_profile_data():
    """Test farming profile data fixture."""
    return {
        "crops_grown": ["rice", "wheat"],
        "farm_size": 5.5,
        "farming_experience": 10,
        "preferred_language": "malayalam"
    }


@pytest.fixture
def test_chat_data():
    """Test chat message data fixture."""
    return {
        "message": "What crops should I grow in this season?",
        "message_type": "text"
    }