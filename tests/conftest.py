"""
Pytest configuration and fixtures for Digital Krishi Officer API tests.
"""

import pytest
import asyncio
import asyncpg
from typing import AsyncGenerator
from unittest.mock import AsyncMock, patch
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
        "crop_types": ["rice", "wheat"],
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


@pytest.fixture
def test_qa_data():
    """Test Q&A repository data fixture."""
    return {
        "question": "What is the best fertilizer for rice crops?",
        "answer": "NPK fertilizer with 4:2:1 ratio works well for rice crops in Kerala.",
        "crop_type": "rice",
        "category": "fertilizer",
        "language": "english"
    }


@pytest.fixture
def test_group_data():
    """Test group chat data fixture."""
    return {
        "name": "Rice Farmers Test Group",
        "description": "Test group for rice farmers",
        "crop_type": "rice",
        "location": "Kerala"
    }


@pytest.fixture
def test_retailer_data():
    """Test retailer data fixture."""
    return {
        "name": "Test Agricultural Store",
        "contact_person": "Test Owner",
        "phone_number": "+91-9876543210",
        "email": "test@teststore.com",
        "address": "Test Address, Kerala",
        "latitude": 10.0,
        "longitude": 76.0,
        "services": ["seeds", "fertilizers", "tools"]
    }


@pytest.fixture
def test_coordinates():
    """Test coordinates fixture for location testing."""
    return {
        "kerala_lat": 10.8505,
        "kerala_lng": 76.2711,
        "kochi_lat": 9.9312,
        "kochi_lng": 76.2673,
        "trivandrum_lat": 8.5241,
        "trivandrum_lng": 76.9366
    }


# N8N Integration Testing Fixtures

@pytest.fixture
def mock_n8n_image_analysis_response():
    """Mock N8N image analysis response."""
    return {
        "status": "success",
        "ai_response": "This appears to be a healthy rice crop with good color and structure.",
        "confidence_score": 0.85,
        "analysis_id": "test-analysis-123",
        "enhanced_processing": True,
        "metadata": {
            "model_used": "gpt-4o-mini",
            "processing_time": "2024-01-15T10:30:00Z",
            "local_context": "Kerala agricultural context applied",
            "seasonal_factors": "Monsoon season considerations"
        },
        "treatment_plan": "Continue current care practices",
        "prevention_measures": "Regular monitoring recommended"
    }


@pytest.fixture
def mock_n8n_batch_response():
    """Mock N8N batch analysis response."""
    return {
        "status": "processing",
        "message": "Enhanced batch analysis started for 3 images",
        "batch_size": 3,
        "workflow_triggered": True,
        "enhanced_processing": True
    }


@pytest.fixture
def mock_n8n_chat_response():
    """Mock N8N enhanced chat response."""
    return {
        "status": "enhanced_response",
        "ai_response": "Based on your location in Kerala and current monsoon season, I recommend planting rice varieties like Jyothi or Pavizham which are well-suited for your region.",
        "trust_score": 0.9,
        "enhanced_processing": True,
        "context_aware": True
    }


@pytest.fixture
def mock_n8n_knowledge_response():
    """Mock N8N knowledge processing response."""
    return {
        "answer": "For rice cultivation in Kerala during monsoon season, use NPK fertilizer in 4:2:1 ratio. Apply 60kg nitrogen, 30kg phosphorus, and 15kg potassium per acre.",
        "source": "enhanced_ai",
        "trust_score": 0.88,
        "enhanced_processing": True,
        "saved_to_kb": True
    }


@pytest.fixture
def mock_n8n_moderation_response():
    """Mock N8N content moderation response."""
    return {
        "action": "approve",
        "confidence_score": 0.95,
        "reasons": ["Content is helpful and appropriate"],
        "moderation_id": "mod-123-456"
    }


@pytest.fixture
def mock_n8n_webhook_response():
    """Mock N8N webhook callback response."""
    return {
        "status": "success",
        "analysis_id": "webhook-test-789",
        "results": {
            "primary_analysis": "Healthy crop identified",
            "confidence_score": 0.87,
            "severity_level": "low",
            "enhanced_analysis": True
        },
        "recommendations": ["Continue current practices", "Monitor for pests"],
        "metadata": {
            "enhanced_by_n8n": True,
            "workflow_version": "1.0"
        }
    }


@pytest.fixture
def mock_httpx_client():
    """Mock httpx.AsyncClient for N8N requests."""

    class MockResponse:
        def __init__(self, json_data, status_code=200):
            self._json_data = json_data
            self.status_code = status_code

        def json(self):
            return self._json_data

        def raise_for_status(self):
            if self.status_code >= 400:
                raise Exception(f"HTTP {self.status_code}")

    class MockAsyncClient:
        def __init__(self, responses=None):
            self.responses = responses or {}
            self.requests = []

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def post(self, url, **kwargs):
            # Log the request for testing
            self.requests.append({
                "url": url,
                "method": "POST",
                "kwargs": kwargs
            })

            # Return appropriate mock response based on URL
            if "analyze-image" in url:
                return MockResponse({
                    "status": "processing",
                    "message": "Enhanced image analysis started",
                    "workflow_triggered": True,
                    "enhanced_processing": True
                })
            elif "batch-analyze" in url:
                return MockResponse({
                    "status": "processing",
                    "message": "Enhanced batch analysis started for 3 images",
                    "batch_size": 3,
                    "workflow_triggered": True
                })
            elif "enhance-chat" in url:
                return MockResponse({
                    "ai_response": "This is a mock enhanced AI response for testing.",
                    "trust_score": 0.85,
                    "enhanced_processing": True
                })
            elif "moderate-content" in url:
                return MockResponse({
                    "action": "approve",
                    "moderation_id": "test-mod-123"
                })
            elif "process-knowledge-query" in url:
                return MockResponse({
                    "ai_response": "Mock knowledge response for testing",
                    "trust_score": 0.9,
                    "saved_to_kb": True
                })
            else:
                return MockResponse({"status": "success"})

    return MockAsyncClient


@pytest.fixture
def mock_n8n_integration():
    """Fixture to mock all N8N integrations."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_instance
        mock_client.return_value.__aexit__ = AsyncMock()

        # Configure mock responses
        mock_instance.post.return_value.status_code = 200
        mock_instance.post.return_value.json.return_value = {
            "status": "success",
            "enhanced_processing": True
        }

        yield mock_instance


@pytest.fixture
def n8n_fallback_mode():
    """Fixture to simulate N8N being unavailable (fallback mode)."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_instance
        mock_client.return_value.__aexit__ = AsyncMock()

        # Simulate N8N being unavailable
        mock_instance.post.side_effect = Exception("N8N service unavailable")

        yield mock_instance