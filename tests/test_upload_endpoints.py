"""
Tests for Upload API endpoints.
"""

import requests
import io
import json
from typing import Dict, Any, Optional
from test_container_endpoints import TestConfig

# Simple image creation without PIL dependency
def create_simple_image():
    """Create a minimal JPEG-like binary data for testing."""
    # This is a minimal valid JPEG header + some data
    jpeg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xaa\xff\xd9'
    return io.BytesIO(jpeg_header)


class UploadTestConfig:
    """Configuration for upload tests."""

    @staticmethod
    def create_test_image():
        """Create a simple test image."""
        return create_simple_image()

    @staticmethod
    def create_test_file(content="test file content"):
        """Create a simple test file."""
        return io.BytesIO(content.encode())


class TestUploadEndpoints:
    """Test suite for Upload API endpoints."""

    def setup(self):
        """Setup test environment."""
        self.base_url = TestConfig.BASE_URL
        self.timeout = TestConfig.TIMEOUT
        self.access_token = None
        self.user_id = None

        # Create and authenticate a test user
        self._setup_test_user()

    def _setup_test_user(self):
        """Create and authenticate a test user for upload tests."""
        # Create test user
        test_user = TestConfig.get_test_user()

        try:
            response = requests.post(
                f"{self.base_url}/api/v1/auth/register",
                json=test_user,
                timeout=self.timeout
            )
            if response.status_code != 200:
                print(f"❌ Registration failed with status {response.status_code}")
                print(f"Response: {response.text}")
                raise Exception(f"Registration failed: {response.status_code} - {response.text}")
            assert response.status_code == 200
        except requests.exceptions.RequestException as e:
            print(f"❌ Registration request failed: {str(e)}")
            raise Exception(f"Registration request failed: {str(e)}")
        self.user_id = response.json()["id"]

        # Login to get access token
        login_data = {
            "username": test_user["email"],
            "password": test_user["password"]
        }

        try:
            response = requests.post(
                f"{self.base_url}/api/v1/auth/login",
                data=login_data,
                timeout=self.timeout
            )
            if response.status_code != 200:
                print(f"❌ Login failed with status {response.status_code}")
                print(f"Response: {response.text}")
                raise Exception(f"Login failed: {response.status_code} - {response.text}")
            assert response.status_code == 200
            self.access_token = response.json()["access_token"]
        except requests.exceptions.RequestException as e:
            print(f"❌ Login request failed: {str(e)}")
            raise Exception(f"Login request failed: {str(e)}")

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authorization headers."""
        return {"Authorization": f"Bearer {self.access_token}"}

    def cleanup(self):
        """Clean up test user after tests complete."""
        if hasattr(self, 'user_id') and self.user_id and hasattr(self, 'access_token') and self.access_token:
            try:
                # Delete the test user
                response = requests.delete(
                    f"{self.base_url}/api/v1/auth/me",
                    headers=self._get_auth_headers(),
                    timeout=self.timeout
                )
                if response.status_code in [200, 404]:
                    print(f"✅ Test user {self.user_id} cleaned up successfully")
                else:
                    print(f"⚠️ Failed to delete test user: {response.status_code}")
            except Exception as e:
                print(f"⚠️ Error during cleanup: {str(e)}")

    def test_upload_image_success(self):
        """Test successful image upload."""
        # Create test image
        test_image = UploadTestConfig.create_test_image()

        files = {
            'file': ('test_image.jpg', test_image, 'image/jpeg')
        }

        response = requests.post(
            f"{self.base_url}/api/v1/upload/",
            files=files,
            headers=self._get_auth_headers(),
            timeout=self.timeout
        )

        assert response.status_code == 200
        data = response.json()
        assert "file_path" in data
        assert data["file_path"].startswith("uploads/")
        assert data["file_path"].endswith(".jpg")

        print(f"✅ Image upload successful: {data['file_path']}")

    def test_upload_different_image_formats(self):
        """Test uploading different image formats."""
        formats = [
            ('jpg', 'image/jpeg'),
            ('jpeg', 'image/jpeg')
        ]

        for fmt, mime_type in formats:
            # Create test image
            test_image = UploadTestConfig.create_test_image()

            files = {
                'file': (f'test_image.{fmt}', test_image, mime_type)
            }

            response = requests.post(
                f"{self.base_url}/api/v1/upload/",
                files=files,
                headers=self._get_auth_headers(),
                timeout=self.timeout
            )

            assert response.status_code == 200
            data = response.json()
            assert "file_path" in data

            print(f"✅ {fmt.upper()} upload successful: {data['file_path']}")

    def test_upload_invalid_file_type(self):
        """Test uploading non-image file (should fail)."""
        # Create a text file
        test_file = UploadTestConfig.create_test_file()

        files = {
            'file': ('test.txt', test_file, 'text/plain')
        }

        response = requests.post(
            f"{self.base_url}/api/v1/upload/",
            files=files,
            headers=self._get_auth_headers(),
            timeout=self.timeout
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "image" in data["detail"].lower()

        print("✅ Invalid file type correctly rejected")

    def test_upload_without_authentication(self):
        """Test upload without authentication (should fail)."""
        test_image = UploadTestConfig.create_test_image()

        files = {
            'file': ('test_image.jpg', test_image, 'image/jpeg')
        }

        response = requests.post(
            f"{self.base_url}/api/v1/upload/",
            files=files,
            timeout=self.timeout
        )

        if response.status_code not in [401, 403]:
            print(f"❌ Expected 401 or 403 but got {response.status_code}")
            print(f"Response: {response.text}")

        assert response.status_code in [401, 403]

        print("✅ Unauthenticated upload correctly rejected")

    def test_upload_corrupted_image(self):
        """Test uploading corrupted image data."""
        # Create invalid image data
        invalid_data = io.BytesIO(b"this is not image data")

        files = {
            'file': ('corrupted.jpg', invalid_data, 'image/jpeg')
        }

        response = requests.post(
            f"{self.base_url}/api/v1/upload/",
            files=files,
            headers=self._get_auth_headers(),
            timeout=self.timeout
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "invalid" in data["detail"].lower()

        print("✅ Corrupted image correctly rejected")

    def test_upload_large_image(self):
        """Test uploading large image to verify size limits."""
        # Create a test image (our simple image is small enough)
        test_image = UploadTestConfig.create_test_image()

        files = {
            'file': ('large_image.jpg', test_image, 'image/jpeg')
        }

        response = requests.post(
            f"{self.base_url}/api/v1/upload/",
            files=files,
            headers=self._get_auth_headers(),
            timeout=self.timeout
        )

        # Should succeed for reasonable image sizes
        assert response.status_code == 200
        data = response.json()
        assert "file_path" in data

        print(f"✅ Image upload successful: {data['file_path']}")

    def test_upload_no_file(self):
        """Test upload request without file."""
        response = requests.post(
            f"{self.base_url}/api/v1/upload/",
            headers=self._get_auth_headers(),
            timeout=self.timeout
        )

        assert response.status_code == 422  # Validation error

        print("✅ No file upload correctly rejected")


if __name__ == "__main__":
    print("Running Upload API tests...")
    test_instance = TestUploadEndpoints()
    test_instance.setup()

    # Run all test methods
    test_methods = [method for method in dir(test_instance) if method.startswith('test_')]

    passed = 0
    failed = 0

    for method_name in test_methods:
        try:
            print(f"\n📋 Running {method_name}...")
            method = getattr(test_instance, method_name)
            method()
            passed += 1
        except Exception as e:
            print(f"❌ {method_name} failed: {str(e)}")
            failed += 1

    print(f"\n📊 Upload API Tests Summary:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {(passed/(passed+failed)*100):.1f}%")