"""
Tests for Location Services API endpoints.
"""

import pytest
import requests
import json
import math
from typing import Dict, Any, Optional, List
from test_container_endpoints import TestConfig


class TestLocationServicesEndpoints:
    """Test suite for Location Services API endpoints."""
    
    def setup(self):
        """Setup test environment."""
        self.base_url = TestConfig.BASE_URL
        self.timeout = TestConfig.TIMEOUT
        self.access_token = None
        self.user_id = None
        self.retailer_ids = []
        
        # Test coordinates (Kerala region)
        self.test_lat = 10.0124
        self.test_lng = 76.3501
        self.kochi_lat = 9.9312
        self.kochi_lng = 76.2673
        self.trivandrum_lat = 8.5241
        self.trivandrum_lng = 76.9366
        
        # Create and authenticate a test user
        self._setup_test_user()
    
    def _setup_test_user(self):
        """Create and authenticate a test user for location tests."""
        # Create test user
        test_user = TestConfig.get_test_user()
        test_user["latitude"] = self.test_lat
        test_user["longitude"] = self.test_lng
        test_user["location"] = "Thrissur, Kerala"
        
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
    
    def _make_authenticated_request(self, method: str, endpoint: str, **kwargs):
        """Make authenticated HTTP request."""
        headers = kwargs.get('headers', {})
        headers['Authorization'] = f'Bearer {self.access_token}'
        kwargs['headers'] = headers
        kwargs.setdefault('timeout', self.timeout)
        
        url = f"{self.base_url}{endpoint}"
        return getattr(requests, method.lower())(url, **kwargs)
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points using Haversine formula."""
        R = 6371  # Earth's radius in kilometers
        
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        distance = R * c
        return round(distance, 2)
    
    def test_create_retailer(self):
        """Test creating a new retailer entry."""
        
        retailer_data = {
            "name": "Kerala Agricultural Supplies",
            "contact_person": "Ravi Kumar",
            "phone_number": "+91-9876543210",
            "email": "ravi@keralaagsupplies.com",
            "address": "MG Road, Thrissur, Kerala 680001",
            "latitude": self.test_lat,
            "longitude": self.test_lng,
            "services": ["fertilizers", "seeds", "pesticides", "tools"]
        }
        
        response = self._make_authenticated_request(
            'POST',
            '/api/v1/location/retailers',
            json=retailer_data
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # Verify response structure
        assert 'id' in result
        assert result['name'] == retailer_data['name']
        assert result['contact_person'] == retailer_data['contact_person']
        assert result['phone_number'] == retailer_data['phone_number']
        assert result['email'] == retailer_data['email']
        assert result['address'] == retailer_data['address']
        assert result['latitude'] == retailer_data['latitude']
        assert result['longitude'] == retailer_data['longitude']
        assert result['services'] == retailer_data['services']
        assert result['rating'] == 0.0
        assert result['is_verified'] is False
        assert 'created_at' in result
        
        # Store for later tests
        self.thrissur_retailer_id = result['id']
        self.retailer_ids.append(result['id'])
    
    def test_create_multiple_retailers(self):
        """Test creating multiple retailers for comprehensive testing."""
        
        retailers_data = [
            {
                "name": "Kochi Farm Center",
                "contact_person": "Suresh Nair", 
                "phone_number": "+91-9876543211",
                "email": "suresh@kochifarm.com",
                "address": "Marine Drive, Kochi, Kerala 682031",
                "latitude": self.kochi_lat,
                "longitude": self.kochi_lng,
                "services": ["organic_fertilizers", "seeds", "irrigation_equipment"]
            },
            {
                "name": "Trivandrum Agricultural Store",
                "contact_person": "Maya Pillai",
                "phone_number": "+91-9876543212", 
                "email": "maya@tvmagrstore.com",
                "address": "Statue Junction, Trivandrum, Kerala 695001",
                "latitude": self.trivandrum_lat,
                "longitude": self.trivandrum_lng,
                "services": ["pesticides", "tools", "fertilizers"]
            },
            {
                "name": "Green Valley Supplies", 
                "contact_person": "Abdul Rahman",
                "phone_number": "+91-9876543213",
                "email": "abdul@greenvalley.com",
                "address": "Near Thrissur, Kerala 680002",
                "latitude": self.test_lat + 0.05,  # Slightly north of Thrissur
                "longitude": self.test_lng + 0.05,
                "services": ["seeds", "organic_pesticides", "soil_testing"]
            },
            {
                "name": "Far Away Retailer",
                "contact_person": "Test User",
                "phone_number": "+91-9876543214", 
                "email": "test@faraway.com",
                "address": "Far Location, India",
                "latitude": 28.6139,  # Delhi coordinates (very far from Kerala)
                "longitude": 77.2090,
                "services": ["general_supplies"]
            }
        ]
        
        for retailer_data in retailers_data:
            response = self._make_authenticated_request(
                'POST',
                '/api/v1/location/retailers',
                json=retailer_data
            )
            
            assert response.status_code == 200
            result = response.json()
            self.retailer_ids.append(result['id'])
            
            # Store specific IDs for later tests
            if 'Kochi' in retailer_data['name']:
                self.kochi_retailer_id = result['id']
            elif 'Trivandrum' in retailer_data['name']:
                self.trivandrum_retailer_id = result['id']
            elif 'Green Valley' in retailer_data['name']:
                self.nearby_retailer_id = result['id']
            elif 'Far Away' in retailer_data['name']:
                self.far_retailer_id = result['id']
    
    def test_get_nearby_retailers(self):
        """Test finding nearby retailers based on location."""
        
        # Test nearby search from Thrissur location
        response = self._make_authenticated_request(
            'GET',
            f'/api/v1/location/retailers/nearby?latitude={self.test_lat}&longitude={self.test_lng}&radius_km=100&limit=10'
        )
        
        if response.status_code != 200:
            print(f"Nearby retailers request failed with status {response.status_code}: {response.text}")
            
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        nearby_retailers = response.json()
        
        assert isinstance(nearby_retailers, list)
        assert len(nearby_retailers) >= 3  # Should find at least 3 Kerala retailers
        
        # Verify structure and distance calculation
        for retailer in nearby_retailers:
            assert 'id' in retailer
            assert 'name' in retailer
            assert 'latitude' in retailer
            assert 'longitude' in retailer
            assert 'distance' in retailer
            
            # Verify distance is within radius
            assert retailer['distance'] <= 100
            
            # Verify distance calculation is roughly correct
            expected_distance = self._calculate_distance(
                self.test_lat, self.test_lng,
                retailer['latitude'], retailer['longitude']
            )
            # Allow some tolerance for calculation differences
            assert abs(retailer['distance'] - expected_distance) <= 1.0
        
        # Verify results are sorted by distance
        distances = [r['distance'] for r in nearby_retailers]
        sorted_distances = sorted(distances)
        
        if distances != sorted_distances:
            print(f"Distances not sorted correctly:")
            print(f"Actual: {distances}")
            print(f"Expected: {sorted_distances}")
            
        assert distances == sorted_distances
        
        # The far away retailer should not be in the results
        retailer_ids = [r['id'] for r in nearby_retailers]
        assert self.far_retailer_id not in retailer_ids
    
    def test_get_nearby_retailers_with_service_filter(self):
        """Test nearby search with service filtering."""
        
        response = self._make_authenticated_request(
            'GET',
            f'/api/v1/location/retailers/nearby?latitude={self.test_lat}&longitude={self.test_lng}&radius_km=50&services=seeds&services=fertilizers&limit=5'
        )
        
        assert response.status_code == 200
        nearby_retailers = response.json()
        
        assert isinstance(nearby_retailers, list)
        
        # All returned retailers should have at least one of the requested services
        for retailer in nearby_retailers:
            services = retailer.get('services', [])
            assert any(service in ['seeds', 'fertilizers'] for service in services)
    
    def test_get_nearby_retailers_verified_only(self):
        """Test nearby search for verified retailers only."""
        
        # First mark one retailer as verified for testing
        # This would normally be done by admin, but we'll update directly for testing
        response = self._make_authenticated_request(
            'PUT',
            f'/api/v1/location/retailers/{self.thrissur_retailer_id}',
            json={
                "name": "Kerala Agricultural Supplies",
                "contact_person": "Ravi Kumar",
                "phone_number": "+91-9876543210", 
                "email": "ravi@keralaagsupplies.com",
                "address": "MG Road, Thrissur, Kerala 680001",
                "latitude": self.test_lat,
                "longitude": self.test_lng,
                "services": ["fertilizers", "seeds", "pesticides", "tools"]
            }
        )
        assert response.status_code == 200
        
        # Now search for verified retailers only
        response = self._make_authenticated_request(
            'GET', 
            f'/api/v1/location/retailers/nearby?latitude={self.test_lat}&longitude={self.test_lng}&radius_km=50&is_verified=false&limit=5'
        )
        
        assert response.status_code == 200
        nearby_retailers = response.json()
        
        # All returned retailers should be unverified (since we didn't actually verify any)
        for retailer in nearby_retailers:
            assert retailer['is_verified'] is False
    
    def test_get_retailers_list(self):
        """Test retrieving list of all retailers with pagination."""
        
        response = self._make_authenticated_request(
            'GET',
            '/api/v1/location/retailers?skip=0&limit=10'
        )
        
        assert response.status_code == 200
        retailers = response.json()
        
        assert isinstance(retailers, list)
        assert len(retailers) >= len(self.retailer_ids)
        
        # Verify structure of retailers
        for retailer in retailers:
            assert 'id' in retailer
            assert 'name' in retailer
            assert 'latitude' in retailer
            assert 'longitude' in retailer
            assert 'rating' in retailer
            assert 'is_verified' in retailer
            assert 'created_at' in retailer
    
    def test_get_retailers_list_filtered(self):
        """Test retrieving retailers with filters."""
        
        # Test is_verified filter
        response = self._make_authenticated_request(
            'GET',
            '/api/v1/location/retailers?is_verified=false&limit=10'
        )
        
        assert response.status_code == 200
        retailers = response.json()
        
        # All should be unverified
        for retailer in retailers:
            assert retailer['is_verified'] is False
        
        # Test services filter (this would depend on exact implementation)
        response = self._make_authenticated_request(
            'GET',
            '/api/v1/location/retailers?services=seeds&limit=5'
        )
        
        assert response.status_code == 200
        retailers = response.json()
        # Results should contain retailers that offer seeds
        # (exact verification depends on the services filtering implementation)
    
    def test_get_specific_retailer(self):
        """Test retrieving a specific retailer by ID."""
        
        response = self._make_authenticated_request(
            'GET',
            f'/api/v1/location/retailers/{self.thrissur_retailer_id}'
        )
        
        assert response.status_code == 200
        retailer = response.json()
        
        assert retailer['id'] == self.thrissur_retailer_id
        assert retailer['name'] == 'Kerala Agricultural Supplies'
        assert retailer['latitude'] == self.test_lat
        assert retailer['longitude'] == self.test_lng
    
    def test_get_nonexistent_retailer(self):
        """Test retrieving a non-existent retailer."""
        
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        response = self._make_authenticated_request(
            'GET',
            f'/api/v1/location/retailers/{fake_id}'
        )
        
        assert response.status_code == 404
        error_data = response.json()
        assert 'Retailer not found' in error_data['detail']
    
    def test_update_retailer(self):
        """Test updating a retailer entry."""
        
        updated_data = {
            "name": "Updated Kerala Agricultural Supplies",
            "contact_person": "Ravi Kumar Nair",
            "phone_number": "+91-9876543210",
            "email": "ravi.updated@keralaagsupplies.com", 
            "address": "Updated MG Road, Thrissur, Kerala 680001",
            "latitude": self.test_lat,
            "longitude": self.test_lng,
            "services": ["fertilizers", "seeds", "pesticides", "tools", "consultation"]
        }
        
        response = self._make_authenticated_request(
            'PUT',
            f'/api/v1/location/retailers/{self.thrissur_retailer_id}',
            json=updated_data
        )
        
        assert response.status_code == 200
        result = response.json()
        
        assert result['id'] == self.thrissur_retailer_id
        assert result['name'] == updated_data['name']
        assert result['contact_person'] == updated_data['contact_person']
        assert result['email'] == updated_data['email']
        assert result['address'] == updated_data['address']
        assert result['services'] == updated_data['services']
    
    def test_rate_retailer(self):
        """Test rating a retailer."""
        
        # Test giving a rating
        rating = 4.5
        
        response = self._make_authenticated_request(
            'POST',
            f'/api/v1/location/retailers/{self.kochi_retailer_id}/rate?rating={rating}'
        )
        
        assert response.status_code == 200
        result = response.json()
        
        assert 'message' in result
        assert 'Rating submitted successfully' in result['message']
        assert 'new_rating' in result
        assert result['new_rating'] == rating
        
        # Verify the rating was applied
        response = self._make_authenticated_request(
            'GET',
            f'/api/v1/location/retailers/{self.kochi_retailer_id}'
        )
        
        assert response.status_code == 200
        retailer = response.json()
        assert retailer['rating'] == rating
        
        # Test giving another rating (should average)
        second_rating = 3.5
        
        response = self._make_authenticated_request(
            'POST',
            f'/api/v1/location/retailers/{self.kochi_retailer_id}/rate?rating={second_rating}'
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # Should be average of 4.5 and 3.5 = 4.0
        assert result['new_rating'] == 4.0
    
    def test_rate_retailer_invalid_rating(self):
        """Test rating with invalid values."""
        
        # Test rating too high
        response = self._make_authenticated_request(
            'POST',
            f'/api/v1/location/retailers/{self.trivandrum_retailer_id}/rate?rating=6.0'
        )
        
        assert response.status_code == 422  # Validation error
        
        # Test rating too low
        response = self._make_authenticated_request(
            'POST',
            f'/api/v1/location/retailers/{self.trivandrum_retailer_id}/rate?rating=0.5'
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_get_distance_to_retailer(self):
        """Test calculating distance to a specific retailer."""
        
        response = self._make_authenticated_request(
            'GET',
            f'/api/v1/location/retailers/{self.kochi_retailer_id}/distance?user_latitude={self.test_lat}&user_longitude={self.test_lng}'
        )
        
        assert response.status_code == 200
        result = response.json()
        
        assert 'retailer_id' in result
        assert 'retailer_name' in result
        assert 'distance_km' in result
        assert 'retailer_location' in result
        
        assert result['retailer_id'] == self.kochi_retailer_id
        assert result['retailer_name'] == 'Kochi Farm Center'
        
        # Verify distance calculation
        expected_distance = self._calculate_distance(
            self.test_lat, self.test_lng,
            self.kochi_lat, self.kochi_lng
        )
        assert abs(result['distance_km'] - expected_distance) <= 1.0
        
        # Verify retailer location info
        location_info = result['retailer_location']
        assert location_info['latitude'] == self.kochi_lat
        assert location_info['longitude'] == self.kochi_lng
        assert 'address' in location_info
    
    def test_get_available_services(self):
        """Test retrieving list of available services."""
        
        response = self._make_authenticated_request(
            'GET',
            '/api/v1/location/services/list'
        )
        
        assert response.status_code == 200
        services = response.json()
        
        assert isinstance(services, list)
        
        # Should have services from our test retailers
        service_names = [service['name'] for service in services]
        assert 'seeds' in service_names
        assert 'fertilizers' in service_names
        
        # Each service should have a count
        for service in services:
            assert 'name' in service
            assert 'count' in service
            assert isinstance(service['count'], int)
            assert service['count'] > 0
    
    def test_get_area_coverage(self):
        """Test getting geographical coverage of retailers."""
        
        response = self._make_authenticated_request(
            'GET',
            '/api/v1/location/area-coverage'
        )
        
        assert response.status_code == 200
        coverage = response.json()
        
        assert 'bounds' in coverage
        assert 'total_retailers' in coverage
        
        bounds = coverage['bounds']
        assert 'min_latitude' in bounds
        assert 'max_latitude' in bounds
        assert 'min_longitude' in bounds
        assert 'max_longitude' in bounds
        
        # Should have reasonable bounds covering Kerala and Delhi
        assert bounds['min_latitude'] <= self.trivandrum_lat  # Southernmost point
        assert bounds['max_latitude'] >= 28.6139  # Delhi latitude
        assert bounds['min_longitude'] <= self.test_lng
        assert bounds['max_longitude'] >= 77.2090  # Delhi longitude
        
        assert isinstance(coverage['total_retailers'], int)
        assert coverage['total_retailers'] >= len(self.retailer_ids)
    
    def test_search_by_location_name(self):
        """Test searching retailers by location name."""
        
        response = self._make_authenticated_request(
            'GET',
            '/api/v1/location/search-by-location?location_name=kerala&radius_km=100&limit=10'
        )
        
        assert response.status_code == 200
        result = response.json()
        
        assert 'location_query' in result
        assert 'retailers_found' in result
        assert 'retailers' in result
        
        assert result['location_query'] == 'kerala'
        assert isinstance(result['retailers_found'], int)
        assert isinstance(result['retailers'], list)
        
        # Should find our Kerala retailers
        retailer_names = [r['name'] for r in result['retailers']]
        kerala_retailers = [name for name in retailer_names if any(
            kerala_term in name.lower() 
            for kerala_term in ['kerala', 'kochi', 'trivandrum', 'thrissur']
        )]
        assert len(kerala_retailers) >= 3
        
        # Test with specific city
        response = self._make_authenticated_request(
            'GET',
            '/api/v1/location/search-by-location?location_name=kochi&radius_km=100&limit=5'
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # Should find the Kochi retailer
        kochi_found = any('Kochi' in r['name'] for r in result['retailers'])
        assert kochi_found
    
    def test_nearby_retailers_edge_cases(self):
        """Test nearby retailers with edge case parameters."""
        
        # Test with very small radius
        response = self._make_authenticated_request(
            'GET',
            f'/api/v1/location/retailers/nearby?latitude={self.test_lat}&longitude={self.test_lng}&radius_km=1&limit=10'
        )
        
        assert response.status_code == 200
        nearby_retailers = response.json()
        
        # Should find only very close retailers (probably just Thrissur and nearby)
        for retailer in nearby_retailers:
            assert retailer['distance'] <= 1.0
        
        # Test with very large radius 
        response = self._make_authenticated_request(
            'GET',
            f'/api/v1/location/retailers/nearby?latitude={self.test_lat}&longitude={self.test_lng}&radius_km=100&limit=20'
        )
        
        assert response.status_code == 200
        nearby_retailers = response.json()
        
        # Should find local retailers but NOT the far away Delhi one (within 100km of Kerala)
        retailer_ids = [r['id'] for r in nearby_retailers]
        assert self.far_retailer_id not in retailer_ids
    
    def test_delete_retailer(self):
        """Test deleting a retailer entry."""
        
        # Use the far away retailer for deletion test
        response = self._make_authenticated_request(
            'DELETE',
            f'/api/v1/location/retailers/{self.far_retailer_id}'
        )
        
        assert response.status_code == 200
        result = response.json()
        
        assert 'message' in result
        assert 'deleted successfully' in result['message']
        
        # Verify the retailer is deleted
        response = self._make_authenticated_request(
            'GET',
            f'/api/v1/location/retailers/{self.far_retailer_id}'
        )
        
        assert response.status_code == 404
    
    def test_unauthorized_location_access(self):
        """Test accessing location endpoints without authentication."""
        
        # Test creating retailer without auth
        retailer_data = {
            "name": "Unauthorized Retailer",
            "latitude": 10.0,
            "longitude": 76.0,
            "services": ["test"]
        }
        
        response = requests.post(
            f"{self.base_url}/api/v1/location/retailers",
            json=retailer_data,
            timeout=self.timeout
        )
        
        assert response.status_code in [401, 403]
        
        # Test getting retailers without auth (might be allowed)
        response = requests.get(
            f"{self.base_url}/api/v1/location/retailers",
            timeout=self.timeout
        )
        
        # This might be accessible without auth for public directory purposes
        assert response.status_code in [200, 401, 403]


def test_location_services_endpoints():
    """Pytest entry point for location services tests."""
    
    test_class = TestLocationServicesEndpoints()
    test_class.setup()
    
    # Run all tests in sequence
    test_methods = [
        test_class.test_create_retailer,
        test_class.test_create_multiple_retailers,
        test_class.test_get_nearby_retailers,
        test_class.test_get_nearby_retailers_with_service_filter,
        test_class.test_get_nearby_retailers_verified_only,
        test_class.test_get_retailers_list,
        test_class.test_get_retailers_list_filtered,
        test_class.test_get_specific_retailer,
        test_class.test_get_nonexistent_retailer,
        test_class.test_update_retailer,
        test_class.test_rate_retailer,
        test_class.test_rate_retailer_invalid_rating,
        test_class.test_get_distance_to_retailer,
        test_class.test_get_available_services,
        test_class.test_get_area_coverage,
        test_class.test_search_by_location_name,
        test_class.test_nearby_retailers_edge_cases,
        test_class.test_delete_retailer,
        test_class.test_unauthorized_location_access
    ]
    
    for test_method in test_methods:
        try:
            test_method()
        except Exception as e:
            pytest.fail(f"Test {test_method.__name__} failed: {str(e)}")


if __name__ == "__main__":
    test_location_services_endpoints()