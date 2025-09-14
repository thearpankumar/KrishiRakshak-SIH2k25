"""
Tests for N8N Webhook API endpoints.
"""

import pytest
import requests
import json
import uuid
from typing import Dict, Any, Optional
from test_container_endpoints import TestConfig


class TestN8NWebhookEndpoints:
    """Test suite for N8N Webhook API endpoints."""

    def setup(self):
        """Setup test environment."""
        self.base_url = TestConfig.BASE_URL
        self.timeout = TestConfig.TIMEOUT

    def test_image_analysis_webhook(self):
        """Test receiving image analysis results from N8N."""

        # Mock N8N image analysis result
        webhook_data = {
            "user_id": str(uuid.uuid4()),
            "image_path": "/uploads/test_crop.jpg",
            "analysis_type": "crop",
            "results": {
                "primary_analysis": "Healthy rice crop with good color and structure",
                "detailed_findings": "The crop shows signs of proper nutrition and adequate water supply",
                "confidence_score": 0.89,
                "severity_level": "low"
            },
            "confidence_score": 0.89,
            "recommendations": [
                "Continue current care practices",
                "Monitor for pest activity during monsoon"
            ],
            "treatment_plan": "Maintain current irrigation schedule",
            "prevention_measures": "Regular field inspection recommended",
            "metadata": {
                "model_used": "gpt-4o-mini",
                "processing_time": "2024-01-15T10:30:00Z",
                "enhanced_by_n8n": True,
                "workflow_version": "1.0",
                "local_context": "Kerala agricultural context",
                "seasonal_factors": "Monsoon season considerations"
            },
            "status": "completed"
        }

        response = requests.post(
            f"{self.base_url}/api/v1/webhooks/image-analysis",
            json=webhook_data,
            headers={
                "Content-Type": "application/json",
                "X-Workflow-Source": "n8n-image-analysis"
            },
            timeout=self.timeout
        )

        assert response.status_code == 200
        result = response.json()

        assert result['status'] == 'success'
        assert 'analysis_id' in result
        # The webhook should save the analysis to the database

    def test_batch_analysis_webhook(self):
        """Test receiving batch analysis results from N8N."""

        batch_webhook_data = {
            "batch_id": f"batch_{uuid.uuid4()}",
            "individual_results": [
                {
                    "user_id": str(uuid.uuid4()),
                    "image_path": "/uploads/batch_img1.jpg",
                    "analysis_type": "pest",
                    "results": {
                        "primary_analysis": "Minor pest activity detected",
                        "confidence_score": 0.75,
                        "severity_level": "medium"
                    },
                    "confidence_score": 0.75,
                    "recommendations": ["Apply organic pesticide"],
                    "image_index": 0
                },
                {
                    "user_id": str(uuid.uuid4()),
                    "image_path": "/uploads/batch_img2.jpg",
                    "analysis_type": "pest",
                    "results": {
                        "primary_analysis": "No pest activity found",
                        "confidence_score": 0.92,
                        "severity_level": "low"
                    },
                    "confidence_score": 0.92,
                    "recommendations": ["Continue monitoring"],
                    "image_index": 1
                }
            ]
        }

        response = requests.post(
            f"{self.base_url}/api/v1/webhooks/batch-complete",
            json=batch_webhook_data,
            headers={
                "Content-Type": "application/json",
                "X-Workflow-Source": "n8n-batch-analysis"
            },
            timeout=self.timeout
        )

        assert response.status_code == 200
        result = response.json()

        assert result['status'] == 'success'
        assert 'batch_id' in result
        assert result['processed_count'] == 2
        assert 'analysis_ids' in result

    def test_content_moderation_webhook(self):
        """Test receiving content moderation results from N8N."""

        moderation_webhook_data = {
            "content_type": "group_message",
            "content_id": str(uuid.uuid4()),
            "moderation_id": f"mod_{uuid.uuid4()}",
            "moderation_result": {
                "action": "approve",
                "confidence_score": 0.95,
                "reasons": ["Content is helpful and appropriate for agricultural discussion"]
            }
        }

        response = requests.post(
            f"{self.base_url}/api/v1/webhooks/community-moderation",
            json=moderation_webhook_data,
            headers={
                "Content-Type": "application/json",
                "X-Workflow-Source": "n8n-content-moderation"
            },
            timeout=self.timeout
        )

        assert response.status_code == 200
        result = response.json()

        assert result['status'] == 'success'
        assert 'moderation_id' in result
        assert result['action_taken'] == 'approve'

    def test_weather_market_update_webhook(self):
        """Test receiving weather and market data from N8N."""

        weather_market_data = {
            "sync_id": f"sync_{uuid.uuid4()}",
            "weather_data": {
                "location": "Kochi, Kerala",
                "temperature": 28.5,
                "humidity": 82,
                "weather_condition": "Monsoon clouds",
                "agricultural_insights": {
                    "planting_recommendation": "Good time for rice planting",
                    "irrigation_advice": "Reduce irrigation due to expected rainfall"
                }
            },
            "market_data": [
                {
                    "commodity": "Rice",
                    "market_name": "Kochi Agricultural Market",
                    "min_price": 2800,
                    "max_price": 3200,
                    "modal_price": 3000,
                    "price_unit": "per quintal"
                }
            ],
            "alerts": [
                {
                    "type": "weather",
                    "severity": "medium",
                    "message": "Heavy rainfall expected in next 48 hours"
                }
            ]
        }

        response = requests.post(
            f"{self.base_url}/api/v1/webhooks/weather-market-update",
            json=weather_market_data,
            headers={
                "Content-Type": "application/json",
                "X-Workflow-Source": "n8n-weather-market"
            },
            timeout=self.timeout
        )

        assert response.status_code == 200
        result = response.json()

        assert result['status'] == 'success'
        assert 'sync_id' in result
        assert result['weather_updated'] == True
        assert result['market_updated'] == True
        assert result['alerts_processed'] == 1

    def test_notification_delivery_webhook(self):
        """Test logging notification delivery status from N8N."""

        notification_log_data = {
            "notification_id": f"notif_{uuid.uuid4()}",
            "user_id": str(uuid.uuid4()),
            "delivery_status": "delivered",
            "delivery_channels": ["push", "email"],
            "delivered_at": "2024-01-15T10:35:00Z"
        }

        response = requests.post(
            f"{self.base_url}/api/v1/webhooks/notification-delivered",
            json=notification_log_data,
            headers={
                "Content-Type": "application/json",
                "X-Log-Type": "notification-delivery"
            },
            timeout=self.timeout
        )

        assert response.status_code == 200
        result = response.json()

        assert result['status'] == 'success'
        assert result['logged'] == True
        assert 'notification_id' in result

    def test_enhanced_chat_webhook(self):
        """Test receiving enhanced chat response from N8N."""

        chat_webhook_data = {
            "user_id": str(uuid.uuid4()),
            "chat_id": f"chat_{uuid.uuid4()}",
            "original_message": "What should I plant this season?",
            "ai_response": "Based on your location in Kerala and the current monsoon season, I recommend planting rice varieties like Jyothi or Pavizham. These varieties are well-suited for Kerala's climate and perform excellently during monsoon periods.",
            "trust_score": 0.91,
            "message_type": "text",
            "metadata": {
                "context_used": ["user_location", "season", "historical_preferences"],
                "model_confidence": 0.91,
                "response_category": "crop_recommendation"
            }
        }

        response = requests.post(
            f"{self.base_url}/api/v1/webhooks/enhanced-chat",
            json=chat_webhook_data,
            headers={
                "Content-Type": "application/json",
                "X-Workflow-Source": "n8n-enhanced-chat"
            },
            timeout=self.timeout
        )

        assert response.status_code == 200
        result = response.json()

        assert result['status'] == 'success'
        assert 'chat_id' in result
        assert 'message_id' in result
        assert 'response' in result
        assert result['trust_score'] == 0.91

    def test_knowledge_query_webhook(self):
        """Test receiving enhanced knowledge query response from N8N."""

        knowledge_webhook_data = {
            "user_id": str(uuid.uuid4()),
            "query_id": f"knowledge_{uuid.uuid4()}",
            "original_question": "How do I prevent fungal diseases in tomatoes?",
            "ai_response": "To prevent fungal diseases in tomatoes in Kerala's climate: 1) Ensure good air circulation between plants, 2) Use drip irrigation to keep leaves dry, 3) Apply copper-based fungicides preventively, 4) Choose disease-resistant varieties like Arka Rakshak, 5) Maintain proper plant spacing.",
            "trust_score": 0.87,
            "crop_type": "tomato",
            "language": "english"
        }

        response = requests.post(
            f"{self.base_url}/api/v1/webhooks/knowledge-query",
            json=knowledge_webhook_data,
            headers={
                "Content-Type": "application/json",
                "X-Workflow-Source": "n8n-knowledge-query"
            },
            timeout=self.timeout
        )

        assert response.status_code == 200
        result = response.json()

        assert result['status'] == 'success'
        assert 'query_id' in result
        assert 'answer' in result
        assert result['trust_score'] == 0.87
        assert 'saved_to_kb' in result

    def test_webhook_invalid_source_header(self):
        """Test webhook with invalid source header."""

        webhook_data = {
            "user_id": str(uuid.uuid4()),
            "test_data": "should be rejected"
        }

        response = requests.post(
            f"{self.base_url}/api/v1/webhooks/image-analysis",
            json=webhook_data,
            headers={
                "Content-Type": "application/json",
                "X-Workflow-Source": "invalid-source"  # Wrong source
            },
            timeout=self.timeout
        )

        assert response.status_code == 401
        error_data = response.json()
        assert 'Invalid workflow source' in error_data['detail']

    def test_webhook_missing_source_header(self):
        """Test webhook without source header."""

        webhook_data = {
            "user_id": str(uuid.uuid4()),
            "test_data": "should be rejected"
        }

        response = requests.post(
            f"{self.base_url}/api/v1/webhooks/image-analysis",
            json=webhook_data,
            headers={"Content-Type": "application/json"},
            # Missing X-Workflow-Source header
            timeout=self.timeout
        )

        assert response.status_code == 401
        error_data = response.json()
        assert 'Invalid workflow source' in error_data['detail']

    def test_webhook_malformed_data(self):
        """Test webhook with malformed data."""

        # Missing required fields
        malformed_data = {
            "incomplete": "data"
            # Missing user_id, image_path, analysis_type, etc.
        }

        response = requests.post(
            f"{self.base_url}/api/v1/webhooks/image-analysis",
            json=malformed_data,
            headers={
                "Content-Type": "application/json",
                "X-Workflow-Source": "n8n-image-analysis"
            },
            timeout=self.timeout
        )

        assert response.status_code == 400
        error_data = response.json()
        assert 'Missing required field' in error_data['detail']

    def test_webhook_health_check(self):
        """Test webhook health check endpoint."""

        response = requests.get(
            f"{self.base_url}/api/v1/webhooks/health",
            timeout=self.timeout
        )

        assert response.status_code == 200
        result = response.json()

        assert result['status'] == 'healthy'
        assert result['service'] == 'webhook-receiver'
        assert 'timestamp' in result
        assert 'endpoints' in result
        assert len(result['endpoints']) >= 7  # Should list all webhook endpoints

    def test_webhook_batch_analysis_empty_results(self):
        """Test batch webhook with empty results array."""

        batch_data = {
            "batch_id": f"batch_{uuid.uuid4()}",
            "individual_results": []  # Empty results
        }

        response = requests.post(
            f"{self.base_url}/api/v1/webhooks/batch-complete",
            json=batch_data,
            headers={
                "Content-Type": "application/json",
                "X-Workflow-Source": "n8n-batch-analysis"
            },
            timeout=self.timeout
        )

        assert response.status_code == 400
        error_data = response.json()
        assert 'Missing or invalid individual_results' in error_data['detail']

    def test_webhook_moderation_reject_action(self):
        """Test content moderation webhook with reject action."""

        moderation_data = {
            "content_type": "group_message",
            "content_id": str(uuid.uuid4()),
            "moderation_id": f"mod_{uuid.uuid4()}",
            "moderation_result": {
                "action": "reject",
                "confidence_score": 0.88,
                "reasons": ["Content contains inappropriate language"]
            }
        }

        response = requests.post(
            f"{self.base_url}/api/v1/webhooks/community-moderation",
            json=moderation_data,
            headers={
                "Content-Type": "application/json",
                "X-Workflow-Source": "n8n-content-moderation"
            },
            timeout=self.timeout
        )

        assert response.status_code == 200
        result = response.json()

        assert result['status'] == 'success'
        assert result['action_taken'] == 'reject'

    def test_webhook_moderation_review_action(self):
        """Test content moderation webhook with review action."""

        moderation_data = {
            "content_type": "group_message",
            "content_id": str(uuid.uuid4()),
            "moderation_id": f"mod_{uuid.uuid4()}",
            "moderation_result": {
                "action": "review",
                "confidence_score": 0.65,
                "reasons": ["Content requires human review for context"]
            }
        }

        response = requests.post(
            f"{self.base_url}/api/v1/webhooks/community-moderation",
            json=moderation_data,
            headers={
                "Content-Type": "application/json",
                "X-Workflow-Source": "n8n-content-moderation"
            },
            timeout=self.timeout
        )

        assert response.status_code == 200
        result = response.json()

        assert result['status'] == 'success'
        assert result['action_taken'] == 'review'


def test_n8n_webhook_endpoints():
    """Pytest entry point for N8N webhook tests."""

    test_class = TestN8NWebhookEndpoints()
    test_class.setup()

    # Run all tests in sequence
    test_methods = [
        test_class.test_image_analysis_webhook,
        test_class.test_batch_analysis_webhook,
        test_class.test_content_moderation_webhook,
        test_class.test_weather_market_update_webhook,
        test_class.test_notification_delivery_webhook,
        test_class.test_enhanced_chat_webhook,
        test_class.test_knowledge_query_webhook,
        test_class.test_webhook_invalid_source_header,
        test_class.test_webhook_missing_source_header,
        test_class.test_webhook_malformed_data,
        test_class.test_webhook_health_check,
        test_class.test_webhook_batch_analysis_empty_results,
        test_class.test_webhook_moderation_reject_action,
        test_class.test_webhook_moderation_review_action
    ]

    for test_method in test_methods:
        try:
            test_method()
        except Exception as e:
            pytest.fail(f"Test {test_method.__name__} failed: {str(e)}")


if __name__ == "__main__":
    test_n8n_webhook_endpoints()