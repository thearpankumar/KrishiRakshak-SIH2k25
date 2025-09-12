"""
Tests for Community Features API endpoints.
"""

import pytest
import requests
import json
from typing import Dict, Any, Optional, List
from test_container_endpoints import TestConfig


class TestCommunityEndpoints:
    """Test suite for Community Features API endpoints."""
    
    def setup(self):
        """Setup test environment."""
        self.base_url = TestConfig.BASE_URL
        self.timeout = TestConfig.TIMEOUT
        self.access_token = None
        self.user_id = None
        self.second_user_token = None
        self.second_user_id = None
        self.group_ids = []
        self.message_ids = []
        
        # Create and authenticate test users
        self._setup_test_users()
    
    def _setup_test_users(self):
        """Create and authenticate multiple test users for community testing."""
        # Create first test user
        test_user1 = TestConfig.get_test_user()
        test_user1["full_name"] = "Community Test User 1"
        
        response = requests.post(
            f"{self.base_url}/api/v1/auth/register",
            json=test_user1,
            timeout=self.timeout
        )
        assert response.status_code == 200
        user_data1 = response.json()
        self.user_id = user_data1["id"]
        
        # Login first user
        login_data1 = {
            "username": test_user1["email"],
            "password": test_user1["password"]
        }
        
        response = requests.post(
            f"{self.base_url}/api/v1/auth/login",
            data=login_data1,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=self.timeout
        )
        assert response.status_code == 200
        login_response1 = response.json()
        self.access_token = login_response1["access_token"]
        
        # Create second test user
        test_user2 = TestConfig.get_test_user()
        test_user2["full_name"] = "Community Test User 2"
        test_user2["location"] = "Kochi, Kerala"
        
        response = requests.post(
            f"{self.base_url}/api/v1/auth/register",
            json=test_user2,
            timeout=self.timeout
        )
        assert response.status_code == 200
        user_data2 = response.json()
        self.second_user_id = user_data2["id"]
        
        # Login second user
        login_data2 = {
            "username": test_user2["email"],
            "password": test_user2["password"]
        }
        
        response = requests.post(
            f"{self.base_url}/api/v1/auth/login",
            data=login_data2,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=self.timeout
        )
        assert response.status_code == 200
        login_response2 = response.json()
        self.second_user_token = login_response2["access_token"]
    
    def _make_authenticated_request(self, method: str, endpoint: str, token: str = None, **kwargs):
        """Make authenticated HTTP request."""
        headers = kwargs.get('headers', {})
        headers['Authorization'] = f'Bearer {token or self.access_token}'
        kwargs['headers'] = headers
        kwargs.setdefault('timeout', self.timeout)
        
        url = f"{self.base_url}{endpoint}"
        return getattr(requests, method.lower())(url, **kwargs)
    
    def test_create_group_chat(self):
        """Test creating a new group chat."""
        
        group_data = {
            "name": "Rice Farmers Kerala",
            "description": "Discussion group for rice farmers in Kerala region",
            "crop_type": "rice",
            "location": "Kerala"
        }
        
        response = self._make_authenticated_request(
            'POST',
            '/api/v1/community/groups',
            json=group_data
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # Verify response structure
        assert 'id' in result
        assert result['name'] == group_data['name']
        assert result['description'] == group_data['description']
        assert result['crop_type'] == group_data['crop_type']
        assert result['location'] == group_data['location']
        assert result['is_active'] is True
        assert 'created_at' in result
        
        # Store for later tests
        self.rice_group_id = result['id']
        self.group_ids.append(result['id'])
    
    def test_create_multiple_group_chats(self):
        """Test creating multiple group chats for comprehensive testing."""
        
        groups_data = [
            {
                "name": "Tomato Growers Association",
                "description": "Support group for tomato cultivation techniques",
                "crop_type": "tomato",
                "location": "Karnataka"
            },
            {
                "name": "Organic Farming Community",
                "description": "Share organic farming methods and experiences",
                "crop_type": "mixed",
                "location": "India"
            },
            {
                "name": "Kochi Farmers Market",
                "description": "Local farmers discussion for market prices and trends",
                "crop_type": None,
                "location": "Kochi"
            }
        ]
        
        for group_data in groups_data:
            response = self._make_authenticated_request(
                'POST',
                '/api/v1/community/groups',
                json=group_data
            )
            
            assert response.status_code == 200
            result = response.json()
            self.group_ids.append(result['id'])
            
            # Store specific IDs for later tests
            if group_data['crop_type'] == 'tomato':
                self.tomato_group_id = result['id']
            elif 'Kochi' in group_data['name']:
                self.kochi_group_id = result['id']
    
    def test_get_group_chats(self):
        """Test retrieving group chats with pagination."""
        
        response = self._make_authenticated_request(
            'GET',
            '/api/v1/community/groups?skip=0&limit=10'
        )
        
        assert response.status_code == 200
        groups = response.json()
        
        assert isinstance(groups, list)
        assert len(groups) >= len(self.group_ids)
        
        # Verify structure of groups
        for group in groups:
            assert 'id' in group
            assert 'name' in group
            assert 'is_active' in group
            assert 'created_at' in group
    
    def test_get_group_chats_filtered(self):
        """Test retrieving group chats with filters."""
        
        # Test crop_type filter
        response = self._make_authenticated_request(
            'GET',
            '/api/v1/community/groups?crop_type=rice&limit=5'
        )
        
        assert response.status_code == 200
        groups = response.json()
        
        # All returned groups should be about rice
        for group in groups:
            assert group['crop_type'] == 'rice'
        
        # Test location filter
        response = self._make_authenticated_request(
            'GET',
            '/api/v1/community/groups?location=kerala&limit=5'
        )
        
        assert response.status_code == 200
        groups = response.json()
        
        # Should find groups with Kerala in location
        found_kerala_group = any(
            'kerala' in (group['location'] or '').lower()
            for group in groups
        )
        assert found_kerala_group
        
        # Test is_active filter
        response = self._make_authenticated_request(
            'GET',
            '/api/v1/community/groups?is_active=true&limit=10'
        )
        
        assert response.status_code == 200
        groups = response.json()
        
        for group in groups:
            assert group['is_active'] is True
    
    def test_get_specific_group_chat(self):
        """Test retrieving a specific group chat by ID."""
        
        response = self._make_authenticated_request(
            'GET',
            f'/api/v1/community/groups/{self.rice_group_id}'
        )
        
        assert response.status_code == 200
        group = response.json()
        
        assert group['id'] == self.rice_group_id
        assert group['crop_type'] == 'rice'
        assert 'Rice Farmers' in group['name']
    
    def test_get_nonexistent_group_chat(self):
        """Test retrieving a non-existent group chat."""
        
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        response = self._make_authenticated_request(
            'GET',
            f'/api/v1/community/groups/{fake_id}'
        )
        
        assert response.status_code == 404
        error_data = response.json()
        assert 'Group chat not found' in error_data['detail']
    
    def test_update_group_chat(self):
        """Test updating a group chat."""
        
        updated_data = {
            "name": "Updated Rice Farmers Kerala",
            "description": "Updated description for rice farmers community",
            "crop_type": "rice",
            "location": "Kerala, India"
        }
        
        response = self._make_authenticated_request(
            'PUT',
            f'/api/v1/community/groups/{self.rice_group_id}',
            json=updated_data
        )
        
        assert response.status_code == 200
        result = response.json()
        
        assert result['id'] == self.rice_group_id
        assert result['name'] == updated_data['name']
        assert result['description'] == updated_data['description']
        assert result['location'] == updated_data['location']
    
    def test_send_group_message(self):
        """Test sending a message to a group chat."""
        
        message_data = {
            "message": "Hello everyone! What's the best time to plant rice this season?",
            "message_type": "text"
        }
        
        # Convert message_data to include group_id as required by schema
        message_with_group = {
            "group_id": self.rice_group_id,
            **message_data
        }
        
        response = self._make_authenticated_request(
            'POST',
            f'/api/v1/community/groups/{self.rice_group_id}/messages',
            json=message_with_group  # API expects message with group_id in body
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # Verify response structure
        assert 'id' in result
        assert result['message'] == message_data['message']
        assert result['message_type'] == message_data['message_type']
        assert result['group_id'] == self.rice_group_id
        assert result['user_id'] == self.user_id
        assert 'created_at' in result
        assert 'user' in result
        assert result['user']['id'] == self.user_id
        
        # Store for later tests
        self.first_message_id = result['id']
        self.message_ids.append(result['id'])
    
    def test_send_multiple_group_messages(self):
        """Test sending multiple messages from different users."""
        
        # Send message from first user
        message1 = {
            "group_id": self.rice_group_id,
            "message": "I usually plant rice in June. What about you all?",
            "message_type": "text"
        }
        
        response = self._make_authenticated_request(
            'POST',
            f'/api/v1/community/groups/{self.rice_group_id}/messages',
            json=message1,
            token=self.access_token
        )
        
        assert response.status_code == 200
        result1 = response.json()
        self.message_ids.append(result1['id'])
        
        # Send message from second user
        message2 = {
            "group_id": self.rice_group_id,
            "message": "July is better in our region due to monsoon patterns.",
            "message_type": "text"
        }
        
        response = self._make_authenticated_request(
            'POST',
            f'/api/v1/community/groups/{self.rice_group_id}/messages',
            json=message2,
            token=self.second_user_token
        )
        
        assert response.status_code == 200
        result2 = response.json()
        
        assert result2['user_id'] == self.second_user_id
        assert result2['message'] == message2['message']
        self.second_user_message_id = result2['id']
        self.message_ids.append(result2['id'])
    
    def test_get_group_messages(self):
        """Test retrieving messages from a group chat."""
        
        response = self._make_authenticated_request(
            'GET',
            f'/api/v1/community/groups/{self.rice_group_id}/messages?skip=0&limit=10'
        )
        
        assert response.status_code == 200
        messages = response.json()
        
        assert isinstance(messages, list)
        assert len(messages) >= 3  # We sent at least 3 messages
        
        # Verify structure of messages
        for message in messages:
            assert 'id' in message
            assert 'message' in message
            assert 'message_type' in message
            assert 'group_id' in message
            assert 'user_id' in message
            assert 'created_at' in message
            assert 'user' in message
            assert message['group_id'] == self.rice_group_id
    
    def test_get_specific_group_message(self):
        """Test retrieving a specific group message."""
        
        response = self._make_authenticated_request(
            'GET',
            f'/api/v1/community/groups/{self.rice_group_id}/messages/{self.first_message_id}'
        )
        
        assert response.status_code == 200
        message = response.json()
        
        assert message['id'] == self.first_message_id
        assert message['group_id'] == self.rice_group_id
        assert 'best time to plant rice' in message['message']
    
    def test_get_nonexistent_group_message(self):
        """Test retrieving a non-existent group message."""
        
        fake_message_id = "00000000-0000-0000-0000-000000000000"
        
        response = self._make_authenticated_request(
            'GET',
            f'/api/v1/community/groups/{self.rice_group_id}/messages/{fake_message_id}'
        )
        
        assert response.status_code == 404
        error_data = response.json()
        assert 'Message not found' in error_data['detail']
    
    def test_delete_own_group_message(self):
        """Test deleting own group message."""
        
        # User should be able to delete their own message
        response = self._make_authenticated_request(
            'DELETE',
            f'/api/v1/community/groups/{self.rice_group_id}/messages/{self.first_message_id}',
            token=self.access_token
        )
        
        assert response.status_code == 200
        result = response.json()
        
        assert 'message' in result
        assert 'deleted successfully' in result['message']
        
        # Verify the message is deleted
        response = self._make_authenticated_request(
            'GET',
            f'/api/v1/community/groups/{self.rice_group_id}/messages/{self.first_message_id}'
        )
        
        assert response.status_code == 404
    
    def test_delete_other_user_message_forbidden(self):
        """Test that users cannot delete other users' messages."""
        
        # Try to delete second user's message with first user's token
        response = self._make_authenticated_request(
            'DELETE',
            f'/api/v1/community/groups/{self.rice_group_id}/messages/{self.second_user_message_id}',
            token=self.access_token
        )
        
        assert response.status_code == 403
        error_data = response.json()
        assert 'You can only delete your own messages' in error_data['detail']
    
    def test_send_message_to_inactive_group(self):
        """Test sending message to inactive/non-existent group."""
        
        fake_group_id = "00000000-0000-0000-0000-000000000000"
        
        message_data = {
            "group_id": fake_group_id,
            "message": "This should fail",
            "message_type": "text"
        }
        
        response = self._make_authenticated_request(
            'POST',
            f'/api/v1/community/groups/{fake_group_id}/messages',
            json=message_data
        )
        
        assert response.status_code == 404
        error_data = response.json()
        assert 'Group chat not found or inactive' in error_data['detail']
    
    def test_get_group_stats(self):
        """Test retrieving group statistics."""
        
        response = self._make_authenticated_request(
            'GET',
            f'/api/v1/community/groups/{self.rice_group_id}/stats'
        )
        
        assert response.status_code == 200
        stats = response.json()
        
        assert 'group_id' in stats
        assert 'group_name' in stats
        assert 'total_messages' in stats
        assert 'active_users_this_week' in stats
        assert 'created_at' in stats
        
        assert stats['group_id'] == self.rice_group_id
        assert isinstance(stats['total_messages'], int)
        assert isinstance(stats['active_users_this_week'], int)
        assert stats['total_messages'] >= 2  # We sent at least 2 remaining messages
    
    def test_discover_groups(self):
        """Test group discovery functionality."""
        
        # Test discovery with crop type preference
        response = self._make_authenticated_request(
            'GET',
            '/api/v1/community/discover?user_crop_types=rice&user_crop_types=tomato&limit=5'
        )
        
        assert response.status_code == 200
        discovery_result = response.json()
        
        assert 'recommended_groups' in discovery_result
        assert 'recommendation_basis' in discovery_result
        
        recommended_groups = discovery_result['recommended_groups']
        assert isinstance(recommended_groups, list)
        
        # Should include our rice and tomato groups
        crop_types_found = [group.get('crop_type') for group in recommended_groups]
        assert 'rice' in crop_types_found or 'tomato' in crop_types_found
        
        # Test discovery with location preference
        response = self._make_authenticated_request(
            'GET',
            '/api/v1/community/discover?user_location=kerala&limit=5'
        )
        
        assert response.status_code == 200
        discovery_result = response.json()
        
        recommended_groups = discovery_result['recommended_groups']
        # Should find groups with Kerala in location
        locations_found = [group.get('location', '').lower() for group in recommended_groups]
        assert any('kerala' in loc for loc in locations_found)
    
    def test_get_my_groups(self):
        """Test retrieving groups where current user has participated."""
        
        response = self._make_authenticated_request(
            'GET',
            '/api/v1/community/my-groups'
        )
        
        assert response.status_code == 200
        my_groups = response.json()
        
        assert isinstance(my_groups, list)
        
        # Should include the rice group where we sent messages
        group_ids_found = [group['id'] for group in my_groups]
        assert self.rice_group_id in group_ids_found
    
    def test_get_activity_feed(self):
        """Test retrieving community activity feed."""
        
        response = self._make_authenticated_request(
            'GET',
            '/api/v1/community/activity-feed?limit=10'
        )
        
        assert response.status_code == 200
        activity_result = response.json()
        
        assert 'activity_feed' in activity_result
        activity_feed = activity_result['activity_feed']
        
        assert isinstance(activity_feed, list)
        
        # Verify activity feed structure
        for activity in activity_feed:
            assert 'id' in activity
            assert 'type' in activity
            assert 'message' in activity
            assert 'user_name' in activity
            assert 'group_name' in activity
            assert 'group_id' in activity
            assert 'created_at' in activity
            assert activity['type'] == 'group_message'
    
    def test_get_popular_topics(self):
        """Test retrieving popular discussion topics."""
        
        response = self._make_authenticated_request(
            'GET',
            '/api/v1/community/popular-topics?days=7'
        )
        
        assert response.status_code == 200
        topics_result = response.json()
        
        assert 'popular_crops' in topics_result
        assert 'popular_locations' in topics_result
        assert 'period_days' in topics_result
        
        assert topics_result['period_days'] == 7
        assert isinstance(topics_result['popular_crops'], list)
        assert isinstance(topics_result['popular_locations'], list)
        
        # Verify structure of popular topics
        for crop in topics_result['popular_crops']:
            assert 'name' in crop
            assert 'activity' in crop
            assert isinstance(crop['activity'], int)
        
        for location in topics_result['popular_locations']:
            assert 'name' in location
            assert 'activity' in location
            assert isinstance(location['activity'], int)
    
    def test_delete_group_chat(self):
        """Test deleting (deactivating) a group chat."""
        
        # Use the Kochi group for deletion test
        response = self._make_authenticated_request(
            'DELETE',
            f'/api/v1/community/groups/{self.kochi_group_id}'
        )
        
        assert response.status_code == 200
        result = response.json()
        
        assert 'message' in result
        assert 'deactivated successfully' in result['message']
        
        # Verify the group is deactivated (should still exist but inactive)
        response = self._make_authenticated_request(
            'GET',
            f'/api/v1/community/groups/{self.kochi_group_id}'
        )
        
        # Group should still exist but be inactive
        if response.status_code == 200:
            group = response.json()
            assert group['is_active'] is False
    
    def test_unauthorized_community_access(self):
        """Test accessing community endpoints without authentication."""
        
        # Test creating group without auth
        group_data = {
            "name": "Unauthorized Group",
            "description": "This should fail"
        }
        
        response = requests.post(
            f"{self.base_url}/api/v1/community/groups",
            json=group_data,
            timeout=self.timeout
        )
        
        assert response.status_code in [401, 403]
        
        # Test getting groups without auth (might be allowed)
        response = requests.get(
            f"{self.base_url}/api/v1/community/groups",
            timeout=self.timeout
        )
        
        # This might be accessible without auth, but posting shouldn't be
        assert response.status_code in [200, 401, 403]


def test_community_endpoints():
    """Pytest entry point for community features tests."""
    
    test_class = TestCommunityEndpoints()
    test_class.setup()
    
    # Run all tests in sequence
    test_methods = [
        test_class.test_create_group_chat,
        test_class.test_create_multiple_group_chats,
        test_class.test_get_group_chats,
        test_class.test_get_group_chats_filtered,
        test_class.test_get_specific_group_chat,
        test_class.test_get_nonexistent_group_chat,
        test_class.test_update_group_chat,
        test_class.test_send_group_message,
        test_class.test_send_multiple_group_messages,
        test_class.test_get_group_messages,
        test_class.test_get_specific_group_message,
        test_class.test_get_nonexistent_group_message,
        test_class.test_delete_own_group_message,
        test_class.test_delete_other_user_message_forbidden,
        test_class.test_send_message_to_inactive_group,
        test_class.test_get_group_stats,
        test_class.test_discover_groups,
        test_class.test_get_my_groups,
        test_class.test_get_activity_feed,
        test_class.test_get_popular_topics,
        test_class.test_delete_group_chat,
        test_class.test_unauthorized_community_access
    ]
    
    for test_method in test_methods:
        try:
            test_method()
        except Exception as e:
            pytest.fail(f"Test {test_method.__name__} failed: {str(e)}")


if __name__ == "__main__":
    test_community_endpoints()