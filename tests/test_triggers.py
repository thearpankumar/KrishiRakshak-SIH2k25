"""
Tests for N8N Trigger API endpoints.
"""

import pytest
import requests
import json
import io
from PIL import Image
from typing import Dict, Any, Optional
from unittest.mock import patch, AsyncMock
from test_container_endpoints import TestConfig


class TestN8NTriggerEndpoints:
    """Test suite for N8N Trigger API endpoints."""

    def setup(self):
        """Setup test environment."""
        self.base_url = TestConfig.BASE_URL
        self.timeout = TestConfig.TIMEOUT
        self.access_token = None
        self.user_id = None

        # Create and authenticate a test user
        self._setup_test_user()

    def _setup_test_user(self):
        """Create and authenticate a test user for trigger tests."""
        # Create test user
        test_user = TestConfig.get_test_user()
        test_user["full_name"] = "N8N Trigger Test User"

        response = requests.post(
            f"{self.base_url}/api/v1/auth/register",
            json=test_user,
            timeout=self.timeout
        )
        assert response.status_code == 200
        user_data = response.json()
        self.user_id = user_data["id"]

        # Login to get access token
        login_data = {
            "username": test_user["email"],
            "password": test_user["password"]
        }

        response = requests.post(
            f"{self.base_url}/api/v1/auth/login",
            data=login_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=self.timeout
        )
        assert response.status_code == 200

        login_response = response.json()
        self.access_token = login_response["access_token"]

        # Create farming profile for better context
        profile_data = {
            "crop_types": ["rice", "tomatoes"],
            "farm_size": 4.0,
            "farming_experience": 8,
            "preferred_language": "english"
        }

        requests.post(
            f"{self.base_url}/api/v1/auth/profile",
            json=profile_data,
            headers={'Authorization': f'Bearer {self.access_token}'},
            timeout=self.timeout
        )

    def _make_authenticated_request(self, method: str, endpoint: str, **kwargs):
        """Make authenticated HTTP request."""
        headers = kwargs.get('headers', {})
        headers['Authorization'] = f'Bearer {self.access_token}'
        kwargs['headers'] = headers
        kwargs.setdefault('timeout', self.timeout)

        url = f"{self.base_url}{endpoint}"
        return getattr(requests, method.lower())(url, **kwargs)

    @staticmethod
    def create_test_image(width=100, height=100, color=(255, 255, 255)):
        """Create a simple test image."""
        img = Image.new('RGB', (width, height), color=color)
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        return img_bytes

    def test_trigger_image_analysis(self):
        """Test triggering image analysis workflow via N8N."""

        with patch('httpx.AsyncClient') as mock_client:
            # Setup mock N8N response
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_client.return_value.__aexit__ = AsyncMock()

            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": "success",
                "message": "Image analysis completed successfully",
                "analysis_id": "n8n-analysis-123",
                "confidence_score": 0.89,
                "enhanced": True
            }
            mock_instance.post.return_value = mock_response

            # Test data
            trigger_data = {
                "image_path": "/uploads/test_image.jpg",
                "analysis_type": "crop",
                "filename": "test_crop.jpg"
            }

            response = self._make_authenticated_request(
                'POST',
                '/api/v1/triggers/analyze-image',
                data=trigger_data
            )

            assert response.status_code == 200
            result = response.json()

            # Verify N8N workflow response
            assert result['status'] == 'success'
            assert result['enhanced'] == True
            assert 'analysis_id' in result
            assert 'confidence_score' in result

            # Verify N8N was called
            mock_client.assert_called_once()

    def test_trigger_batch_analysis(self):
        """Test triggering batch analysis workflow via N8N."""

        with patch('httpx.AsyncClient') as mock_client:
            # Setup mock N8N response
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_client.return_value.__aexit__ = AsyncMock()

            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": "success",
                "message": "Batch analysis started successfully",
                "batch_id": "batch-n8n-456",
                "images_queued": 3
            }
            mock_instance.post.return_value = mock_response

            # Test data
            batch_data = {
                "analysis_type": "pest",
                "image_data": [
                    {"image_path": "/uploads/img1.jpg", "filename": "pest1.jpg"},
                    {"image_path": "/uploads/img2.jpg", "filename": "pest2.jpg"},
                    {"image_path": "/uploads/img3.jpg", "filename": "pest3.jpg"}
                ]
            }

            response = self._make_authenticated_request(
                'POST',
                '/api/v1/triggers/batch-analyze',
                data=batch_data
            )

            assert response.status_code == 200
            result = response.json()

            # Verify batch workflow response
            assert result['status'] == 'success'
            assert 'batch_id' in result
            assert result['images_queued'] == 3

            # Verify N8N was called
            mock_client.assert_called_once()

    def test_trigger_content_moderation(self):
        """Test triggering content moderation workflow via N8N."""

        with patch('httpx.AsyncClient') as mock_client:
            # Setup mock N8N response
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_client.return_value.__aexit__ = AsyncMock()

            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "action": "approve",
                "moderation_id": "mod-n8n-789",
                "confidence_score": 0.95,
                "reasons": ["Content is appropriate and helpful"]
            }
            mock_instance.post.return_value = mock_response

            # Test data
            moderation_data = {
                "content": "What's the best time to plant rice in Kerala?",
                "content_type": "group_message",
                "group_id": "test-group-123"
            }

            response = self._make_authenticated_request(
                'POST',
                '/api/v1/triggers/moderate-content',
                data=moderation_data
            )

            assert response.status_code == 200
            result = response.json()

            # Verify moderation workflow response
            assert result['action'] == 'approve'
            assert 'moderation_id' in result
            assert 'confidence_score' in result

            # Verify N8N was called
            mock_client.assert_called_once()

    def test_trigger_smart_notification(self):
        """Test triggering smart notification workflow via N8N."""

        with patch('httpx.AsyncClient') as mock_client:
            # Setup mock N8N response
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_client.return_value.__aexit__ = AsyncMock()

            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": "success",
                "notification_id": "notif-n8n-012",
                "delivery_channels": ["push", "email"],
                "scheduled_at": "2024-01-15T10:30:00Z"
            }
            mock_instance.post.return_value = mock_response

            # Test data
            notification_data = {
                "notification_type": "weather_alert",
                "message": "Heavy rainfall expected tomorrow. Protect your crops!",
                "priority": "high",
                "metadata": {"weather_event": "heavy_rain"}
            }

            response = self._make_authenticated_request(
                'POST',
                '/api/v1/triggers/send-notification',
                data=notification_data
            )

            assert response.status_code == 200
            result = response.json()

            # Verify notification workflow response
            assert result['status'] == 'success'
            assert 'notification_id' in result
            assert 'delivery_channels' in result

            # Verify N8N was called
            mock_client.assert_called_once()

    def test_trigger_weather_update(self):
        """Test triggering weather and market data update workflow via N8N."""

        with patch('httpx.AsyncClient') as mock_client:
            # Setup mock N8N response
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_client.return_value.__aexit__ = AsyncMock()

            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": "success",
                "sync_id": "weather-sync-345",
                "data_sources": ["openweather", "government_apis"],
                "updated_locations": 5
            }
            mock_instance.post.return_value = mock_response

            # Test data
            weather_data = {
                "location": "Kochi, Kerala",
                "latitude": 9.9312,
                "longitude": 76.2673
            }

            response = self._make_authenticated_request(
                'POST',
                '/api/v1/triggers/update-weather',
                data=weather_data
            )

            assert response.status_code == 200
            result = response.json()

            # Verify weather update workflow response
            assert result['status'] == 'success'
            assert 'sync_id' in result
            assert 'data_sources' in result

            # Verify N8N was called
            mock_client.assert_called_once()

    def test_trigger_enhanced_chat(self):
        """Test triggering enhanced chat processing workflow via N8N."""

        with patch('httpx.AsyncClient') as mock_client:
            # Setup mock N8N response
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_client.return_value.__aexit__ = AsyncMock()

            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "ai_response": "Based on your location in Kerala and the upcoming monsoon season, I recommend planting rice varieties like Jyothi or Pavizham which are well-suited for high rainfall areas.",
                "trust_score": 0.92,
                "enhanced_processing": True,
                "context_aware": True
            }
            mock_instance.post.return_value = mock_response

            # Test data
            chat_data = {
                "message": "What crop should I plant next month?",
                "message_type": "text",
                "context": {"season": "monsoon", "previous_crop": "wheat"}
            }

            response = self._make_authenticated_request(
                'POST',
                '/api/v1/triggers/enhance-chat',
                data=chat_data
            )

            assert response.status_code == 200
            result = response.json()

            # Verify enhanced chat workflow response
            assert 'ai_response' in result
            assert result['enhanced_processing'] == True
            assert result['context_aware'] == True
            assert 'trust_score' in result

            # Verify N8N was called
            mock_client.assert_called_once()

    def test_trigger_knowledge_query(self):
        """Test triggering knowledge processing workflow via N8N."""

        with patch('httpx.AsyncClient') as mock_client:
            # Setup mock N8N response
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_client.return_value.__aexit__ = AsyncMock()

            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "ai_response": "For tomato cultivation in Kerala, use a balanced NPK fertilizer with a 19:19:19 ratio during vegetative growth, then switch to 13:0:45 during flowering and fruiting stages.",
                "trust_score": 0.88,
                "saved_to_kb": True,
                "query_id": "knowledge-n8n-678"
            }
            mock_instance.post.return_value = mock_response

            # Test data
            knowledge_data = {
                "question": "What fertilizer should I use for tomatoes?",
                "crop_type": "tomato",
                "language": "english"
            }

            response = self._make_authenticated_request(
                'POST',
                '/api/v1/triggers/process-knowledge-query',
                data=knowledge_data
            )

            assert response.status_code == 200
            result = response.json()

            # Verify knowledge processing workflow response
            assert 'ai_response' in result
            assert result['saved_to_kb'] == True
            assert 'trust_score' in result
            assert 'query_id' in result

            # Verify N8N was called
            mock_client.assert_called_once()

    def test_trigger_invalid_analysis_type(self):
        """Test trigger with invalid analysis type."""

        # Test data with invalid analysis type
        invalid_data = {
            "image_path": "/uploads/test.jpg",
            "analysis_type": "invalid_type",
            "filename": "test.jpg"
        }

        response = self._make_authenticated_request(
            'POST',
            '/api/v1/triggers/analyze-image',
            data=invalid_data
        )

        assert response.status_code == 400
        error_data = response.json()
        assert 'Invalid analysis type' in error_data['detail']

    def test_trigger_n8n_unavailable(self):
        """Test trigger behavior when N8N is unavailable."""

        with patch('httpx.AsyncClient') as mock_client:
            # Setup mock to simulate N8N unavailable
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_client.return_value.__aexit__ = AsyncMock()

            # Simulate N8N service unavailable
            import httpx
            mock_instance.post.side_effect = httpx.RequestError("N8N service unavailable")

            trigger_data = {
                "image_path": "/uploads/test.jpg",
                "analysis_type": "crop",
                "filename": "test.jpg"
            }

            response = self._make_authenticated_request(
                'POST',
                '/api/v1/triggers/analyze-image',
                data=trigger_data
            )

            # Should return error when N8N is unavailable
            assert response.status_code == 503
            error_data = response.json()
            assert 'Failed to call N8N' in error_data['detail']

    def test_trigger_health_check(self):
        """Test N8N connectivity health check."""

        with patch('httpx.AsyncClient') as mock_client:
            # Setup mock N8N health response
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_client.return_value.__aexit__ = AsyncMock()

            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_instance.get.return_value = mock_response

            response = self._make_authenticated_request(
                'GET',
                '/api/v1/triggers/health'
            )

            assert response.status_code == 200
            result = response.json()

            assert 'status' in result
            assert 'timestamp' in result

    def test_unauthorized_trigger_access(self):
        """Test accessing trigger endpoints without authentication."""

        trigger_data = {
            "image_path": "/uploads/test.jpg",
            "analysis_type": "crop",
            "filename": "test.jpg"
        }

        # Request without authorization header
        response = requests.post(
            f"{self.base_url}/api/v1/triggers/analyze-image",
            data=trigger_data,
            timeout=self.timeout
        )

        assert response.status_code in [401, 403]  # Unauthorized or Forbidden


def test_n8n_trigger_endpoints():
    """Pytest entry point for N8N trigger tests."""

    test_class = TestN8NTriggerEndpoints()
    test_class.setup()

    # Run all tests in sequence
    test_methods = [
        test_class.test_trigger_image_analysis,
        test_class.test_trigger_batch_analysis,
        test_class.test_trigger_content_moderation,
        test_class.test_trigger_smart_notification,
        test_class.test_trigger_weather_update,
        test_class.test_trigger_enhanced_chat,
        test_class.test_trigger_knowledge_query,
        test_class.test_trigger_invalid_analysis_type,
        test_class.test_trigger_n8n_unavailable,
        test_class.test_trigger_health_check,
        test_class.test_unauthorized_trigger_access
    ]

    for test_method in test_methods:
        try:
            test_method()
        except Exception as e:
            pytest.fail(f"Test {test_method.__name__} failed: {str(e)}")


if __name__ == "__main__":
    test_n8n_trigger_endpoints()