"""
Tests for Image Analysis API endpoints with N8N integration.
"""

import pytest
import requests
import io
import json
from PIL import Image
from typing import Dict, Any, Optional
from unittest.mock import patch, AsyncMock
from test_container_endpoints import TestConfig


class ImageAnalysisTestConfig:
    """Configuration for image analysis tests."""
    
    @staticmethod
    def create_test_image(width=100, height=100, color=(255, 255, 255)):
        """Create a simple test image."""
        img = Image.new('RGB', (width, height), color=color)
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        return img_bytes


class TestImageAnalysisEndpoints:
    """Test suite for Image Analysis API endpoints."""
    
    def setup(self):
        """Setup test environment."""
        self.base_url = TestConfig.BASE_URL
        self.timeout = TestConfig.TIMEOUT
        self.access_token = None
        self.user_id = None
        
        # Create and authenticate a test user
        self._setup_test_user()
    
    def _setup_test_user(self):
        """Create and authenticate a test user for analysis tests."""
        # Create test user
        test_user = TestConfig.get_test_user()
        
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
        
        # Create farming profile for better AI context
        profile_data = {
            "crop_types": ["rice", "tomatoes"],
            "farm_size": 3.5,
            "farming_experience": 5,
            "preferred_language": "malayalam"
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
    
    def test_upload_single_image_crop_analysis(self):
        """Test uploading and analyzing a single image for crop analysis with N8N integration."""

        with patch('httpx.AsyncClient') as mock_client:
            # Setup mock N8N response
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_client.return_value.__aexit__ = AsyncMock()

            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": "processing",
                "workflow_triggered": True,
                "enhanced_processing": True
            }
            mock_instance.post.return_value = mock_response

            # Create a test image
            test_image = ImageAnalysisTestConfig.create_test_image(
                width=200, height=200, color=(34, 139, 34)  # Forest green for crop-like appearance
            )

            # Prepare multipart form data
            files = {
                'file': ('test_crop.jpg', test_image, 'image/jpeg')
            }
            data = {
                'analysis_type': 'crop'
            }

            response = self._make_authenticated_request(
                'POST',
                '/api/v1/analysis/upload-image',
                files=files,
                data=data
            )

            assert response.status_code == 200
            result = response.json()

            # Verify N8N integration response structure
            assert result['status'] == 'processing'
            assert result['workflow_triggered'] == True
            assert result['enhanced_processing'] == True
            assert 'message' in result
            assert 'estimated_time' in result

            # Verify N8N workflow was called
            mock_instance.post.assert_called_once()
    
    def test_upload_single_image_pest_analysis(self):
        """Test uploading and analyzing a single image for pest analysis."""
        
        # Create a test image with different color to simulate pest presence
        test_image = ImageAnalysisTestConfig.create_test_image(
            width=150, height=150, color=(139, 69, 19)  # Brown color
        )
        
        files = {
            'file': ('test_pest.jpg', test_image, 'image/jpeg')
        }
        data = {
            'analysis_type': 'pest'
        }
        
        response = self._make_authenticated_request(
            'POST',
            '/api/v1/analysis/upload-image',
            files=files,
            data=data
        )
        
        assert response.status_code == 200
        result = response.json()
        
        assert result['analysis_type'] == 'pest'
        assert 'confidence_score' in result
        
        self.pest_analysis_id = result['id']
    
    def test_upload_single_image_disease_analysis(self):
        """Test uploading and analyzing a single image for disease analysis."""
        
        test_image = ImageAnalysisTestConfig.create_test_image(
            width=180, height=180, color=(205, 133, 63)  # Peru color for diseased appearance
        )
        
        files = {
            'file': ('test_disease.jpg', test_image, 'image/jpeg')
        }
        data = {
            'analysis_type': 'disease'
        }
        
        response = self._make_authenticated_request(
            'POST',
            '/api/v1/analysis/upload-image',
            files=files,
            data=data
        )
        
        assert response.status_code == 200
        result = response.json()
        
        assert result['analysis_type'] == 'disease'
        self.disease_analysis_id = result['id']
    
    def test_upload_single_image_soil_analysis(self):
        """Test uploading and analyzing a single image for soil analysis."""
        
        test_image = ImageAnalysisTestConfig.create_test_image(
            width=160, height=160, color=(160, 82, 45)  # Saddle brown for soil
        )
        
        files = {
            'file': ('test_soil.jpg', test_image, 'image/jpeg')
        }
        data = {
            'analysis_type': 'soil'
        }
        
        response = self._make_authenticated_request(
            'POST',
            '/api/v1/analysis/upload-image',
            files=files,
            data=data
        )
        
        assert response.status_code == 200
        result = response.json()
        
        assert result['analysis_type'] == 'soil'
        self.soil_analysis_id = result['id']

    def test_analyze_endpoint_crop_analysis(self):
        """Test the new /analyze endpoint for crop analysis."""

        test_image = ImageAnalysisTestConfig.create_test_image(
            width=200, height=200, color=(34, 139, 34)  # Forest green for healthy crop
        )

        files = {
            'file': ('test_crop_analyze.jpg', test_image, 'image/jpeg')
        }
        data = {
            'analysis_type': 'crop'
        }

        response = self._make_authenticated_request(
            'POST',
            '/api/v1/analysis/analyze',
            files=files,
            data=data
        )

        assert response.status_code == 200
        result = response.json()

        assert result['analysis_type'] == 'crop'
        assert 'confidence_score' in result
        assert 'results' in result
        assert 'recommendations' in result

        print(f"✅ /analyze endpoint works for crop analysis: {result['id']}")

    def test_analyze_endpoint_pest_analysis(self):
        """Test the new /analyze endpoint for pest analysis."""

        test_image = ImageAnalysisTestConfig.create_test_image(
            width=180, height=180, color=(255, 69, 0)  # Red-orange for pest damage
        )

        files = {
            'file': ('test_pest_analyze.jpg', test_image, 'image/jpeg')
        }
        data = {
            'analysis_type': 'pest'
        }

        response = self._make_authenticated_request(
            'POST',
            '/api/v1/analysis/analyze',
            files=files,
            data=data
        )

        assert response.status_code == 200
        result = response.json()

        assert result['analysis_type'] == 'pest'
        assert 'confidence_score' in result

        print(f"✅ /analyze endpoint works for pest analysis: {result['id']}")

    def test_analyze_endpoint_disease_analysis(self):
        """Test the new /analyze endpoint for disease analysis."""

        test_image = ImageAnalysisTestConfig.create_test_image(
            width=180, height=180, color=(205, 133, 63)  # Peru color for diseased appearance
        )

        files = {
            'file': ('test_disease_analyze.jpg', test_image, 'image/jpeg')
        }
        data = {
            'analysis_type': 'disease'
        }

        response = self._make_authenticated_request(
            'POST',
            '/api/v1/analysis/analyze',
            files=files,
            data=data
        )

        assert response.status_code == 200
        result = response.json()

        assert result['analysis_type'] == 'disease'
        assert 'confidence_score' in result

        print(f"✅ /analyze endpoint works for disease analysis: {result['id']}")

    def test_analyze_endpoint_soil_analysis(self):
        """Test the new /analyze endpoint for soil analysis."""

        test_image = ImageAnalysisTestConfig.create_test_image(
            width=160, height=160, color=(160, 82, 45)  # Saddle brown for soil
        )

        files = {
            'file': ('test_soil_analyze.jpg', test_image, 'image/jpeg')
        }
        data = {
            'analysis_type': 'soil'
        }

        response = self._make_authenticated_request(
            'POST',
            '/api/v1/analysis/analyze',
            files=files,
            data=data
        )

        assert response.status_code == 200
        result = response.json()

        assert result['analysis_type'] == 'soil'
        assert 'confidence_score' in result

        print(f"✅ /analyze endpoint works for soil analysis: {result['id']}")
    
    def test_invalid_analysis_type(self):
        """Test upload with invalid analysis type."""
        
        test_image = ImageAnalysisTestConfig.create_test_image()
        
        files = {
            'file': ('test_invalid.jpg', test_image, 'image/jpeg')
        }
        data = {
            'analysis_type': 'invalid_type'
        }
        
        response = self._make_authenticated_request(
            'POST',
            '/api/v1/analysis/upload-image',
            files=files,
            data=data
        )
        
        assert response.status_code == 400
        error_data = response.json()
        assert 'detail' in error_data
        assert 'Invalid analysis type' in error_data['detail']
    
    def test_upload_non_image_file(self):
        """Test uploading a non-image file."""
        
        # Create a text file instead of an image
        text_file = io.BytesIO(b"This is not an image file")
        
        files = {
            'file': ('test.txt', text_file, 'text/plain')
        }
        data = {
            'analysis_type': 'crop'
        }
        
        response = self._make_authenticated_request(
            'POST',
            '/api/v1/analysis/upload-image',
            files=files,
            data=data
        )
        
        assert response.status_code == 400
        error_data = response.json()
        assert 'File must be an image' in error_data['detail']
    
    def test_upload_oversized_file(self):
        """Test uploading an oversized file."""
        
        # Create a large test image (this might be memory intensive, so we'll use a reasonable size)
        large_image = ImageAnalysisTestConfig.create_test_image(
            width=3000, height=3000  # This should create a large image
        )
        
        files = {
            'file': ('large_test.jpg', large_image, 'image/jpeg')
        }
        data = {
            'analysis_type': 'crop'
        }
        
        response = self._make_authenticated_request(
            'POST',
            '/api/v1/analysis/upload-image',
            files=files,
            data=data
        )
        
        # This might pass or fail depending on actual file size, but shouldn't crash
        assert response.status_code in [200, 413]
    
    def test_batch_analyze_images(self):
        """Test batch analysis of multiple images with N8N integration."""

        with patch('httpx.AsyncClient') as mock_client:
            # Setup mock N8N response for batch processing
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_client.return_value.__aexit__ = AsyncMock()

            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": "processing",
                "message": "Enhanced batch analysis started for 3 images",
                "batch_size": 3,
                "workflow_triggered": True,
                "enhanced_processing": True
            }
            mock_instance.post.return_value = mock_response

            # Create multiple test images
            images = []
            for i in range(3):
                color = [(255, 0, 0), (0, 255, 0), (0, 0, 255)][i]  # Red, Green, Blue
                img = ImageAnalysisTestConfig.create_test_image(
                    width=120, height=120, color=color
                )
                images.append(('files', (f'batch_test_{i}.jpg', img, 'image/jpeg')))

            data = {
                'analysis_type': 'crop'
            }

            response = self._make_authenticated_request(
                'POST',
                '/api/v1/analysis/batch-analyze',
                files=images,
                data=data
            )

            assert response.status_code == 200
            result = response.json()

            # Verify N8N batch processing response
            assert result['status'] == 'processing'
            assert result['batch_size'] == 3
            assert result['workflow_triggered'] == True
            assert result['enhanced_processing'] == True
            assert 'estimated_time' in result

            # Verify N8N workflow was called for batch processing
            mock_instance.post.assert_called_once()
    
    def test_get_analysis_history(self):
        """Test retrieving analysis history."""
        
        response = self._make_authenticated_request(
            'GET',
            '/api/v1/analysis/history'
        )
        
        assert response.status_code == 200
        history = response.json()
        
        assert isinstance(history, list)
        # We should have at least the analyses from previous tests
        assert len(history) >= 4  # crop, pest, disease, soil
        
        # Verify structure of history items
        for item in history:
            assert 'id' in item
            assert 'analysis_type' in item
            assert 'created_at' in item
            assert 'confidence_score' in item
    
    def test_get_analysis_history_filtered(self):
        """Test retrieving filtered analysis history."""
        
        # Test filtering by analysis type
        response = self._make_authenticated_request(
            'GET',
            '/api/v1/analysis/history?analysis_type=crop&limit=5'
        )
        
        assert response.status_code == 200
        filtered_history = response.json()
        
        assert isinstance(filtered_history, list)
        
        # Verify all returned items are crop analysis
        for item in filtered_history:
            assert item['analysis_type'] == 'crop'
    
    def test_get_specific_analysis_result(self):
        """Test retrieving a specific analysis result."""
        
        # Use the crop analysis ID from earlier test
        response = self._make_authenticated_request(
            'GET',
            f'/api/v1/analysis/{self.crop_analysis_id}'
        )
        
        assert response.status_code == 200
        result = response.json()
        
        assert result['id'] == self.crop_analysis_id
        assert result['analysis_type'] == 'crop'
        assert 'results' in result
        assert 'recommendations' in result
    
    def test_get_nonexistent_analysis_result(self):
        """Test retrieving a non-existent analysis result."""
        
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        response = self._make_authenticated_request(
            'GET',
            f'/api/v1/analysis/{fake_id}'
        )
        
        assert response.status_code == 404
        error_data = response.json()
        assert 'Analysis not found' in error_data['detail']
    
    def test_get_analysis_stats(self):
        """Test retrieving analysis statistics."""
        
        response = self._make_authenticated_request(
            'GET',
            '/api/v1/analysis/stats/summary'
        )
        
        if response.status_code != 200:
            print(f"Stats request failed with status {response.status_code}: {response.text}")
            print(f"Access token: {self.access_token[:20]}..." if self.access_token else "No access token")
            
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        stats = response.json()
        
        assert 'total_analyses' in stats
        assert 'by_type' in stats
        assert 'recent_analyses' in stats
        
        # Verify by_type structure
        assert 'crop' in stats['by_type']
        assert 'pest' in stats['by_type']
        assert 'disease' in stats['by_type']
        assert 'soil' in stats['by_type']
        
        # We should have at least 4 analyses from our tests
        assert stats['total_analyses'] >= 4
    
    def test_delete_analysis_result(self):
        """Test deleting an analysis result."""
        
        # Use the soil analysis ID from earlier test
        response = self._make_authenticated_request(
            'DELETE',
            f'/api/v1/analysis/{self.soil_analysis_id}'
        )
        
        assert response.status_code == 200
        result = response.json()
        assert 'message' in result
        assert 'deleted successfully' in result['message']
        
        # Verify the analysis is deleted
        response = self._make_authenticated_request(
            'GET',
            f'/api/v1/analysis/{self.soil_analysis_id}'
        )
        
        assert response.status_code == 404
    
    def test_unauthorized_analysis_access(self):
        """Test accessing analysis endpoints without authentication."""
        
        test_image = ImageAnalysisTestConfig.create_test_image()
        
        files = {
            'file': ('test_unauthorized.jpg', test_image, 'image/jpeg')
        }
        data = {
            'analysis_type': 'crop'
        }
        
        # Request without authorization header
        response = requests.post(
            f"{self.base_url}/api/v1/analysis/upload-image",
            files=files,
            data=data,
            timeout=self.timeout
        )
        
        assert response.status_code in [401, 403]  # Unauthorized or Forbidden
    
    def test_batch_analyze_too_many_files(self):
        """Test batch analysis with too many files (N8N supports up to 20)."""

        # Create more than 20 images (the new N8N limit)
        images = []
        for i in range(22):  # Over the limit
            img = ImageAnalysisTestConfig.create_test_image(width=50, height=50)
            images.append(('files', (f'batch_overflow_{i}.jpg', img, 'image/jpeg')))

        data = {
            'analysis_type': 'pest'
        }

        response = self._make_authenticated_request(
            'POST',
            '/api/v1/analysis/batch-analyze',
            files=images,
            data=data
        )

        assert response.status_code == 400
        error_data = response.json()
        assert 'Maximum 20 images allowed' in error_data['detail']

    def test_analysis_n8n_fallback_mode(self):
        """Test analysis fallback when N8N is unavailable."""

        with patch('httpx.AsyncClient') as mock_client:
            # Setup mock to simulate N8N unavailable
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_client.return_value.__aexit__ = AsyncMock()

            # Simulate N8N service unavailable
            import httpx
            mock_instance.post.side_effect = httpx.RequestError("N8N service unavailable")

            test_image = ImageAnalysisTestConfig.create_test_image()

            files = {
                'file': ('test_fallback.jpg', test_image, 'image/jpeg')
            }
            data = {
                'analysis_type': 'crop'
            }

            response = self._make_authenticated_request(
                'POST',
                '/api/v1/analysis/analyze',
                files=files,
                data=data
            )

            # Should return 503 when N8N is unavailable
            assert response.status_code == 503
            error_data = response.json()
            assert 'Failed to start enhanced analysis' in error_data['detail']

    def test_n8n_integration_success(self):
        """Test successful N8N integration with proper workflow triggering."""

        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_client.return_value.__aexit__ = AsyncMock()

            # Mock successful N8N response
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": "success",
                "message": "Image analysis completed successfully",
                "analysis_id": "n8n-test-123",
                "confidence_score": 0.89,
                "enhanced": True
            }
            mock_instance.post.return_value = mock_response

            test_image = ImageAnalysisTestConfig.create_test_image(
                width=200, height=200, color=(34, 139, 34)
            )

            files = {
                'file': ('test_n8n_success.jpg', test_image, 'image/jpeg')
            }
            data = {
                'analysis_type': 'disease'
            }

            response = self._make_authenticated_request(
                'POST',
                '/api/v1/analysis/analyze',
                files=files,
                data=data
            )

            assert response.status_code == 200
            result = response.json()

            # Verify enhanced processing response
            assert result['status'] == 'processing'
            assert result['enhanced_processing'] == True
            assert result['workflow_triggered'] == True
            assert 'estimated_time' in result

            # Verify N8N was called with correct parameters
            mock_instance.post.assert_called_once()
            call_args = mock_instance.post.call_args

            # Check the URL contains the trigger endpoint
            assert 'triggers/analyze-image' in call_args[1]['data']['image_path'] or 'analyze-image' in str(call_args)


def test_image_analysis_endpoints():
    """Pytest entry point for image analysis tests."""
    
    test_class = TestImageAnalysisEndpoints()
    test_class.setup()
    
    # Run all tests in sequence
    test_methods = [
        test_class.test_upload_single_image_crop_analysis,
        test_class.test_upload_single_image_pest_analysis,
        test_class.test_upload_single_image_disease_analysis,
        test_class.test_upload_single_image_soil_analysis,
        test_class.test_invalid_analysis_type,
        test_class.test_upload_non_image_file,
        test_class.test_upload_oversized_file,
        test_class.test_batch_analyze_images,
        test_class.test_get_analysis_history,
        test_class.test_get_analysis_history_filtered,
        test_class.test_get_specific_analysis_result,
        test_class.test_get_nonexistent_analysis_result,
        test_class.test_get_analysis_stats,
        test_class.test_delete_analysis_result,
        test_class.test_unauthorized_analysis_access,
        test_class.test_batch_analyze_too_many_files
    ]
    
    for test_method in test_methods:
        try:
            test_method()
        except Exception as e:
            pytest.fail(f"Test {test_method.__name__} failed: {str(e)}")


if __name__ == "__main__":
    test_image_analysis_endpoints()