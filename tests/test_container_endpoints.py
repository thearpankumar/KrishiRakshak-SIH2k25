"""
Comprehensive test suite for Digital Krishi Officer FastAPI endpoints.
Tests all endpoints using container/production environment setup.
"""

import pytest
import requests
import asyncio
import json
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import uuid


class TestConfig:
    """Test configuration for container testing."""
    
    BASE_URL = "http://localhost:8000"  # Container URL
    TIMEOUT = 30
    
    # Test user data
    TEST_USER = {
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "testpassword123",
        "phone_number": "+1234567890",
        "location": "Test Location",
        "latitude": 10.0,
        "longitude": 76.0
    }
    
    TEST_PROFILE = {
        "crops_grown": ["rice", "wheat"],
        "farm_size": 5.5,
        "farming_experience": 10,
        "preferred_language": "malayalam"
    }
    
    TEST_CHAT = {
        "message": "What crops should I grow in this season?",
        "message_type": "text"
    }


class DigitalKrishiTester:
    """Main test class for Digital Krishi Officer API endpoints."""
    
    def __init__(self):
        self.base_url = TestConfig.BASE_URL
        self.timeout = TestConfig.TIMEOUT
        self.access_token: Optional[str] = None
        self.user_id: Optional[str] = None
        self.test_results: Dict[str, Any] = {}
        
    def make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make HTTP request with proper error handling."""
        url = f"{self.base_url}{endpoint}"
        headers = kwargs.get('headers', {})
        
        if self.access_token and 'Authorization' not in headers:
            headers['Authorization'] = f"Bearer {self.access_token}"
        
        kwargs['headers'] = headers
        kwargs.setdefault('timeout', self.timeout)
        
        try:
            response = getattr(requests, method.lower())(url, **kwargs)
            return response
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Request failed: {e}")
    
    def assert_response(self, response: requests.Response, expected_status: int, 
                       description: str) -> Dict[str, Any]:
        """Assert response status and return JSON data."""
        try:
            data = response.json()
        except json.JSONDecodeError:
            data = {"text": response.text}
        
        self.test_results[description] = {
            "status_code": response.status_code,
            "expected_status": expected_status,
            "success": response.status_code == expected_status,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        if response.status_code != expected_status:
            error_msg = (
                f"{description} failed:\n"
                f"Expected: {expected_status}\n"
                f"Got: {response.status_code}\n"
                f"Response: {data}"
            )
            pytest.fail(error_msg)
        
        return data

    def test_health_endpoints(self):
        """Test basic health and info endpoints."""
        
        # Test root endpoint
        response = self.make_request('GET', '/')
        data = self.assert_response(response, 200, "Root endpoint")
        assert "message" in data
        assert "Digital Krishi Officer API" in data["message"]
        
        # Test health endpoint
        response = self.make_request('GET', '/health')
        data = self.assert_response(response, 200, "Health endpoint")
        assert data["status"] == "healthy"
        assert "service" in data

    def test_user_registration(self):
        """Test user registration endpoint."""
        
        # Test successful registration
        response = self.make_request(
            'POST', 
            '/api/v1/auth/register',
            json=TestConfig.TEST_USER
        )
        data = self.assert_response(response, 200, "User registration")
        
        assert data["email"] == TestConfig.TEST_USER["email"]
        assert data["full_name"] == TestConfig.TEST_USER["full_name"]
        assert "id" in data
        assert "created_at" in data
        assert data["is_active"] is True
        
        self.user_id = data["id"]
        
        # Test duplicate registration (should fail)
        response = self.make_request(
            'POST',
            '/api/v1/auth/register', 
            json=TestConfig.TEST_USER
        )
        self.assert_response(response, 400, "Duplicate registration")

    def test_user_login(self):
        """Test user login endpoint."""
        
        login_data = {
            "username": TestConfig.TEST_USER["email"],
            "password": TestConfig.TEST_USER["password"]
        }
        
        response = self.make_request(
            'POST',
            '/api/v1/auth/login',
            data=login_data,  # OAuth2PasswordRequestForm expects form data
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        data = self.assert_response(response, 200, "User login")
        
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        
        self.access_token = data["access_token"]
        
        # Test invalid login
        invalid_login = {
            "username": TestConfig.TEST_USER["email"],
            "password": "wrongpassword"
        }
        
        response = self.make_request(
            'POST',
            '/api/v1/auth/login',
            data=invalid_login,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        self.assert_response(response, 401, "Invalid login")

    def test_user_profile_endpoints(self):
        """Test user profile CRUD endpoints."""
        
        # Test get current user
        response = self.make_request('GET', '/api/v1/auth/me')
        data = self.assert_response(response, 200, "Get current user")
        assert data["email"] == TestConfig.TEST_USER["email"]
        
        # Test update user profile
        update_data = {
            "full_name": "Updated Test User",
            "location": "Updated Location"
        }
        
        response = self.make_request(
            'PUT',
            '/api/v1/auth/me',
            json=update_data
        )
        data = self.assert_response(response, 200, "Update user profile")
        assert data["full_name"] == update_data["full_name"]
        assert data["location"] == update_data["location"]

    def test_farming_profile_endpoints(self):
        """Test farming profile CRUD endpoints."""
        
        # Test create farming profile
        response = self.make_request(
            'POST',
            '/api/v1/auth/profile',
            json=TestConfig.TEST_PROFILE
        )
        data = self.assert_response(response, 200, "Create farming profile")
        
        assert data["crops_grown"] == TestConfig.TEST_PROFILE["crops_grown"]
        assert data["farm_size"] == TestConfig.TEST_PROFILE["farm_size"]
        assert data["farming_experience"] == TestConfig.TEST_PROFILE["farming_experience"]
        
        # Test get farming profile
        response = self.make_request('GET', '/api/v1/auth/profile')
        data = self.assert_response(response, 200, "Get farming profile")
        assert data["crops_grown"] == TestConfig.TEST_PROFILE["crops_grown"]
        
        # Test update farming profile
        update_data = {
            "crops_grown": ["rice", "corn", "tomatoes"],
            "farm_size": 7.5
        }
        
        response = self.make_request(
            'PUT',
            '/api/v1/auth/profile',
            json=update_data
        )
        data = self.assert_response(response, 200, "Update farming profile")
        assert data["crops_grown"] == update_data["crops_grown"]
        assert data["farm_size"] == update_data["farm_size"]
        
        # Test duplicate profile creation (should fail)
        response = self.make_request(
            'POST',
            '/api/v1/auth/profile',
            json=TestConfig.TEST_PROFILE
        )
        self.assert_response(response, 400, "Duplicate profile creation")

    def test_chat_endpoints(self):
        """Test chat/AI endpoints."""
        
        # Test send chat message
        response = self.make_request(
            'POST',
            '/api/v1/chat/',
            json=TestConfig.TEST_CHAT
        )
        data = self.assert_response(response, 200, "Send chat message")
        
        assert data["message"] == TestConfig.TEST_CHAT["message"]
        assert data["message_type"] == TestConfig.TEST_CHAT["message_type"]
        assert "response" in data
        assert "id" in data
        assert "created_at" in data
        
        message_id = data["id"]
        
        # Test get specific chat message
        response = self.make_request('GET', f'/api/v1/chat/{message_id}')
        data = self.assert_response(response, 200, "Get specific chat message")
        assert data["id"] == message_id
        
        # Test get chat history
        response = self.make_request('GET', '/api/v1/chat/history')
        data = self.assert_response(response, 200, "Get chat history")
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Test get chat history with pagination
        response = self.make_request(
            'GET', 
            '/api/v1/chat/history?limit=10&offset=0'
        )
        data = self.assert_response(response, 200, "Get chat history with pagination")
        assert isinstance(data, list)
        
        # Test delete specific chat message
        response = self.make_request('DELETE', f'/api/v1/chat/{message_id}')
        data = self.assert_response(response, 200, "Delete chat message")
        assert "message" in data
        
        # Send another message for clear history test
        self.make_request('POST', '/api/v1/chat/', json=TestConfig.TEST_CHAT)
        
        # Test clear chat history
        response = self.make_request('DELETE', '/api/v1/chat/history/clear')
        data = self.assert_response(response, 200, "Clear chat history")
        assert "message" in data

    def test_unauthorized_access(self):
        """Test endpoints without authentication."""
        
        # Temporarily remove token
        temp_token = self.access_token
        self.access_token = None
        
        # Test protected endpoints without token
        protected_endpoints = [
            ('GET', '/api/v1/auth/me'),
            ('PUT', '/api/v1/auth/me'),
            ('POST', '/api/v1/auth/profile'),
            ('GET', '/api/v1/auth/profile'),
            ('POST', '/api/v1/chat/'),
            ('GET', '/api/v1/chat/history'),
        ]
        
        for method, endpoint in protected_endpoints:
            response = self.make_request(method, endpoint, json={})
            self.assert_response(
                response, 
                401, 
                f"Unauthorized access to {method} {endpoint}"
            )
        
        # Restore token
        self.access_token = temp_token

    def test_invalid_data_handling(self):
        """Test endpoints with invalid data."""
        
        # Test invalid registration data
        invalid_user = {
            "email": "invalid-email",
            "full_name": "",
            "password": "123"  # Too short
        }
        
        response = self.make_request(
            'POST',
            '/api/v1/auth/register',
            json=invalid_user
        )
        self.assert_response(response, 422, "Invalid registration data")
        
        # Test invalid chat message
        invalid_chat = {
            "message": "",  # Empty message
            "message_type": "invalid_type"
        }
        
        response = self.make_request(
            'POST',
            '/api/v1/chat/',
            json=invalid_chat
        )
        # This might return 422 for validation error or 200 if AI service handles it
        # We'll just verify it doesn't crash
        assert response.status_code in [200, 422, 400]

    def run_all_tests(self):
        """Run all test suites in order."""
        
        print(f"\n🚀 Starting Digital Krishi Officer API Tests")
        print(f"🔗 Testing against: {self.base_url}")
        print("=" * 60)
        
        try:
            # Basic connectivity tests
            print("\n1. Testing health endpoints...")
            self.test_health_endpoints()
            
            # Authentication tests
            print("2. Testing user registration...")
            self.test_user_registration()
            
            print("3. Testing user login...")
            self.test_user_login()
            
            # User profile tests
            print("4. Testing user profile endpoints...")
            self.test_user_profile_endpoints()
            
            # Farming profile tests
            print("5. Testing farming profile endpoints...")
            self.test_farming_profile_endpoints()
            
            # Chat/AI tests
            print("6. Testing chat endpoints...")
            self.test_chat_endpoints()
            
            # Security tests
            print("7. Testing unauthorized access...")
            self.test_unauthorized_access()
            
            # Data validation tests
            print("8. Testing invalid data handling...")
            self.test_invalid_data_handling()
            
            print("\n" + "=" * 60)
            print("✅ ALL TESTS PASSED!")
            
            # Print summary
            successful_tests = sum(1 for result in self.test_results.values() 
                                 if result['success'])
            total_tests = len(self.test_results)
            
            print(f"📊 Test Summary: {successful_tests}/{total_tests} tests passed")
            
            return True
            
        except Exception as e:
            print(f"\n❌ TEST SUITE FAILED: {str(e)}")
            return False
        
        finally:
            self.print_detailed_results()

    def print_detailed_results(self):
        """Print detailed test results."""
        
        print("\n" + "=" * 60)
        print("📋 DETAILED TEST RESULTS")
        print("=" * 60)
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"\n{status} {test_name}")
            print(f"   Status: {result['status_code']} (expected: {result['expected_status']})")
            
            if not result['success']:
                print(f"   Data: {result['data']}")
        
        # Save results to file
        with open('test_results.json', 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        print(f"\n💾 Full results saved to test_results.json")


def test_container_endpoints():
    """Main test function for pytest integration."""
    
    tester = DigitalKrishiTester()
    success = tester.run_all_tests()
    
    if not success:
        pytest.fail("Container endpoint tests failed")


def main():
    """Run tests directly (non-pytest mode)."""
    
    tester = DigitalKrishiTester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()