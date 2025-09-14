"""
Tests for Knowledge Repository API endpoints with N8N integration.
"""

import pytest
import requests
import json
from typing import Dict, Any, Optional
from unittest.mock import patch, AsyncMock
from test_container_endpoints import TestConfig


class TestKnowledgeRepositoryEndpoints:
    """Test suite for Knowledge Repository API endpoints."""
    
    def setup(self):
        """Setup test environment."""
        self.base_url = TestConfig.BASE_URL
        self.timeout = TestConfig.TIMEOUT
        self.access_token = None
        self.user_id = None
        self.qa_entries = []
        
        # Create and authenticate a test user
        self._setup_test_user()
    
    def _setup_test_user(self):
        """Create and authenticate a test user for knowledge tests."""
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
    
    def _make_authenticated_request(self, method: str, endpoint: str, **kwargs):
        """Make authenticated HTTP request."""
        headers = kwargs.get('headers', {})
        headers['Authorization'] = f'Bearer {self.access_token}'
        kwargs['headers'] = headers
        kwargs.setdefault('timeout', self.timeout)
        
        url = f"{self.base_url}{endpoint}"
        return getattr(requests, method.lower())(url, **kwargs)
    
    def test_create_qa_entry(self):
        """Test creating a new Q&A entry."""
        
        qa_data = {
            "question": "What is the best fertilizer for rice crops in Kerala?",
            "answer": "For rice crops in Kerala, organic compost mixed with NPK fertilizer (4:2:1 ratio) works best. Apply during the tillering stage for optimal growth.",
            "crop_type": "rice",
            "category": "fertilizer",
            "language": "english"
        }
        
        response = self._make_authenticated_request(
            'POST',
            '/api/v1/knowledge/',
            json=qa_data
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # Verify response structure
        assert 'id' in result
        assert result['question'] == qa_data['question']
        assert result['answer'] == qa_data['answer']
        assert result['crop_type'] == qa_data['crop_type']
        assert result['category'] == qa_data['category']
        assert result['language'] == qa_data['language']
        assert result['upvotes'] == 0
        assert result['downvotes'] == 0
        assert 'created_at' in result
        
        # Store for later tests
        self.rice_qa_id = result['id']
        self.qa_entries.append(result)
    
    def test_create_multiple_qa_entries(self):
        """Test creating multiple Q&A entries for comprehensive testing."""
        
        qa_entries = [
            {
                "question": "How to identify pest attacks on tomato plants?",
                "answer": "Look for yellowing leaves, small holes in fruits, and presence of insects. Common pests include aphids, whiteflies, and fruit borers.",
                "crop_type": "tomato",
                "category": "pest",
                "language": "english"
            },
            {
                "question": "What are the symptoms of bacterial wilt in tomatoes?",
                "answer": "Bacterial wilt causes sudden wilting of plants, brown streaks in stems, and bacterial ooze when stems are cut. Remove infected plants immediately.",
                "crop_type": "tomato", 
                "category": "disease",
                "language": "english"
            },
            {
                "question": "Best irrigation method for wheat farming?",
                "answer": "Drip irrigation or furrow irrigation works best for wheat. Water requirement is 450-600mm throughout the growing season.",
                "crop_type": "wheat",
                "category": "irrigation",
                "language": "english"
            },
            {
                "question": "കേരളത്തിൽ തെങ്ങിന്റെ കീടനാശിനി എങ്ങനെ തിരിച്ചറിയാം?",
                "answer": "തെങ്ങിന്റെ ഇലകളിൽ മഞ്ഞനിറം, ഇലകൾ വരണ്ടുപോകൽ, കൊമ്പുകളിൽ കുഴികൾ എന്നിവ കീടബാധയുടെ ലക്ഷണങ്ങളാണ്.",
                "crop_type": "coconut",
                "category": "pest",
                "language": "malayalam"
            }
        ]
        
        for qa_data in qa_entries:
            response = self._make_authenticated_request(
                'POST',
                '/api/v1/knowledge/',
                json=qa_data
            )
            
            assert response.status_code == 200
            result = response.json()
            self.qa_entries.append(result)
            
            # Store specific IDs for later tests
            if qa_data['crop_type'] == 'tomato' and qa_data['category'] == 'pest':
                self.tomato_pest_qa_id = result['id']
            elif qa_data['language'] == 'malayalam':
                self.malayalam_qa_id = result['id']
    
    def test_get_qa_entries(self):
        """Test retrieving Q&A entries with pagination."""
        
        response = self._make_authenticated_request(
            'GET',
            '/api/v1/knowledge/?skip=0&limit=10'
        )
        
        assert response.status_code == 200
        entries = response.json()
        
        assert isinstance(entries, list)
        assert len(entries) >= len(self.qa_entries)
        
        # Verify structure of entries
        for entry in entries:
            assert 'id' in entry
            assert 'question' in entry
            assert 'answer' in entry
            assert 'upvotes' in entry
            assert 'downvotes' in entry
            assert 'created_at' in entry
    
    def test_get_qa_entries_filtered(self):
        """Test retrieving Q&A entries with filters."""
        
        # Test crop_type filter
        response = self._make_authenticated_request(
            'GET',
            '/api/v1/knowledge/?crop_type=tomato&limit=5'
        )
        
        assert response.status_code == 200
        entries = response.json()
        
        assert isinstance(entries, list)
        # All returned entries should be about tomato
        for entry in entries:
            assert entry['crop_type'] == 'tomato'
        
        # Test category filter
        response = self._make_authenticated_request(
            'GET',
            '/api/v1/knowledge/?category=pest&limit=5'
        )
        
        assert response.status_code == 200
        entries = response.json()
        
        for entry in entries:
            assert entry['category'] == 'pest'
        
        # Test language filter
        response = self._make_authenticated_request(
            'GET',
            '/api/v1/knowledge/?language=malayalam&limit=5'
        )
        
        assert response.status_code == 200
        entries = response.json()
        
        for entry in entries:
            assert entry['language'] == 'malayalam'
    
    def test_get_specific_qa_entry(self):
        """Test retrieving a specific Q&A entry by ID."""
        
        response = self._make_authenticated_request(
            'GET',
            f'/api/v1/knowledge/{self.rice_qa_id}'
        )
        
        assert response.status_code == 200
        entry = response.json()
        
        assert entry['id'] == self.rice_qa_id
        assert entry['crop_type'] == 'rice'
        assert 'fertilizer' in entry['question'].lower()
    
    def test_get_nonexistent_qa_entry(self):
        """Test retrieving a non-existent Q&A entry."""
        
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        response = self._make_authenticated_request(
            'GET',
            f'/api/v1/knowledge/{fake_id}'
        )
        
        assert response.status_code == 404
        error_data = response.json()
        assert 'Q&A entry not found' in error_data['detail']
    
    def test_search_knowledge_vector_search(self):
        """Test knowledge search with vector search enabled."""
        
        # Search for rice-related questions
        search_query = "rice fertilizer best practice"
        
        response = self._make_authenticated_request(
            'GET',
            f'/api/v1/knowledge/search?query={search_query}&use_vector_search=true&limit=5'
        )
        
        assert response.status_code == 200
        results = response.json()
        
        assert isinstance(results, list)
        
        # Should return results with similarity scores
        for result in results:
            assert 'id' in result
            assert 'question' in result
            assert 'answer' in result
            # Vector search results should have similarity scores
            if 'similarity_score' in result:
                assert isinstance(result['similarity_score'], (int, float))
                assert 0 <= result['similarity_score'] <= 1
    
    def test_search_knowledge_traditional_search(self):
        """Test knowledge search with traditional search."""
        
        search_query = "tomato pest"
        
        response = self._make_authenticated_request(
            'GET',
            f'/api/v1/knowledge/search?query={search_query}&use_vector_search=false&limit=5'
        )
        
        assert response.status_code == 200
        results = response.json()
        
        assert isinstance(results, list)
        # Should find our tomato pest entry
        found_tomato_pest = any(
            'tomato' in result['question'].lower() and 'pest' in result['question'].lower()
            for result in results
        )
        assert found_tomato_pest
    
    def test_search_knowledge_with_filters(self):
        """Test knowledge search with additional filters."""
        
        search_query = "pest"
        
        response = self._make_authenticated_request(
            'GET',
            f'/api/v1/knowledge/search?query={search_query}&crop_type=tomato&category=pest&limit=3'
        )
        
        assert response.status_code == 200
        results = response.json()
        
        assert isinstance(results, list)
        # All results should match the filters
        for result in results:
            assert result['crop_type'] == 'tomato'
            assert result['category'] == 'pest'
    
    def test_update_qa_entry(self):
        """Test updating a Q&A entry."""
        
        updated_data = {
            "question": "What is the best organic fertilizer for rice crops in Kerala?",
            "answer": "For rice crops in Kerala, cow dung compost mixed with vermicompost and neem cake works best. Apply during the tillering stage for optimal organic growth.",
            "crop_type": "rice",
            "category": "organic_fertilizer",
            "language": "english"
        }
        
        response = self._make_authenticated_request(
            'PUT',
            f'/api/v1/knowledge/{self.rice_qa_id}',
            json=updated_data
        )
        
        assert response.status_code == 200
        result = response.json()
        
        assert result['id'] == self.rice_qa_id
        assert result['question'] == updated_data['question']
        assert result['answer'] == updated_data['answer']
        assert result['category'] == updated_data['category']
        
        # Verify the update persisted
        response = self._make_authenticated_request(
            'GET',
            f'/api/v1/knowledge/{self.rice_qa_id}'
        )
        
        assert response.status_code == 200
        updated_entry = response.json()
        assert updated_entry['question'] == updated_data['question']
    
    def test_vote_on_qa_entry(self):
        """Test voting on Q&A entries."""
        
        # Test upvote
        response = self._make_authenticated_request(
            'POST',
            f'/api/v1/knowledge/{self.tomato_pest_qa_id}/vote?vote_type=upvote'
        )
        
        assert response.status_code == 200
        vote_result = response.json()
        
        assert 'message' in vote_result
        assert 'upvoted' in vote_result['message']
        assert 'upvotes' in vote_result
        assert 'downvotes' in vote_result
        assert vote_result['upvotes'] >= 1
        
        # Test downvote on the same entry
        response = self._make_authenticated_request(
            'POST',
            f'/api/v1/knowledge/{self.tomato_pest_qa_id}/vote?vote_type=downvote'
        )
        
        assert response.status_code == 200
        vote_result = response.json()
        
        assert 'downvoted' in vote_result['message']
        assert vote_result['downvotes'] >= 1
    
    def test_invalid_vote_type(self):
        """Test voting with invalid vote type."""
        
        response = self._make_authenticated_request(
            'POST',
            f'/api/v1/knowledge/{self.rice_qa_id}/vote?vote_type=invalid_vote'
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_ask_ai_question(self):
        """Test asking a question to AI with N8N enhanced knowledge processing."""

        with patch('httpx.AsyncClient') as mock_client:
            # Setup mock N8N knowledge processing response
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_client.return_value.__aexit__ = AsyncMock()

            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "ai_response": "For preventing fungal diseases in rice during monsoon, use resistant varieties like Jyothi, ensure proper drainage, apply propiconazole fungicide, and maintain field sanitation.",
                "trust_score": 0.92,
                "saved_to_kb": True
            }
            mock_instance.post.return_value = mock_response

            ai_question = "How do I prevent fungal diseases in rice crops during monsoon?"

            response = self._make_authenticated_request(
                'POST',
                f'/api/v1/knowledge/ask-ai?question={ai_question}&crop_type=rice&language=english'
            )

            assert response.status_code == 200
            ai_result = response.json()

            assert 'answer' in ai_result
            assert 'source' in ai_result
            assert ai_result['source'] == 'enhanced_ai'
            assert ai_result['enhanced_processing'] == True
            assert 'trust_score' in ai_result
            assert isinstance(ai_result['trust_score'], (int, float))
            assert ai_result['saved_to_kb'] == True

            # Verify N8N was called
            mock_instance.post.assert_called_once()

    def test_ask_ai_question_fallback(self):
        """Test asking AI question when N8N is unavailable (fallback mode)."""

        with patch('httpx.AsyncClient') as mock_client:
            # Setup mock to simulate N8N unavailable
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_client.return_value.__aexit__ = AsyncMock()

            # Simulate N8N service unavailable
            import httpx
            mock_instance.post.side_effect = httpx.RequestError("N8N knowledge service unavailable")

            ai_question = "What's the best fertilizer for tomato plants?"

            response = self._make_authenticated_request(
                'POST',
                f'/api/v1/knowledge/ask-ai?question={ai_question}&crop_type=tomato&language=english'
            )

            assert response.status_code == 200
            ai_result = response.json()

            assert 'answer' in ai_result
            assert 'source' in ai_result
            assert ai_result['source'] == 'fallback'
            assert ai_result['enhanced_processing'] == False
            assert ai_result['fallback_mode'] == True
            assert 'trust_score' in ai_result

            # Verify N8N was attempted
            mock_instance.post.assert_called_once()

    def test_ask_ai_with_knowledge_base_match(self):
        """Test AI question when knowledge base has similar entries."""

        # First, let's assume there are similar questions in the knowledge base
        # This would simulate the vector search finding high-similarity matches

        ai_question = "What is the best fertilizer for rice crops?"

        # Mock both vector service and N8N (if needed)
        with patch('app.services.vector_service.vector_service.search_similar_questions') as mock_vector:
            # Mock high similarity match - should return from knowledge base
            mock_vector.return_value = [{
                "qa_id": "test-123",
                "answer": "NPK fertilizer with 4:2:1 ratio works well for rice crops in Kerala.",
                "similarity_score": 0.95
            }]

            response = self._make_authenticated_request(
                'POST',
                f'/api/v1/knowledge/ask-ai?question={ai_question}&crop_type=rice&language=english'
            )

            assert response.status_code == 200
            ai_result = response.json()

            # Should return from knowledge base without calling N8N
            assert ai_result['source'] == 'knowledge_base'
            assert ai_result['enhanced_processing'] == False
            assert 'similarity_score' in ai_result
            assert ai_result['similarity_score'] == 0.95
    
    def test_get_categories_list(self):
        """Test retrieving available categories."""
        
        response = self._make_authenticated_request(
            'GET',
            '/api/v1/knowledge/categories/list'
        )
        
        assert response.status_code == 200
        categories = response.json()
        
        assert isinstance(categories, list)
        
        # Should have categories from our test data
        category_names = [cat['name'] for cat in categories]
        assert 'pest' in category_names
        assert 'fertilizer' in category_names or 'organic_fertilizer' in category_names
        
        # Each category should have a count
        for category in categories:
            assert 'name' in category
            assert 'count' in category
            assert isinstance(category['count'], int)
            assert category['count'] > 0
    
    def test_get_crops_list(self):
        """Test retrieving available crop types."""
        
        response = self._make_authenticated_request(
            'GET',
            '/api/v1/knowledge/crops/list'
        )
        
        assert response.status_code == 200
        crops = response.json()
        
        assert isinstance(crops, list)
        
        # Should have crop types from our test data
        crop_names = [crop['name'] for crop in crops]
        assert 'rice' in crop_names
        assert 'tomato' in crop_names
        
        # Each crop should have a count
        for crop in crops:
            assert 'name' in crop
            assert 'count' in crop
            assert isinstance(crop['count'], int)
            assert crop['count'] > 0

    def test_get_popular_questions(self):
        """Test retrieving popular questions."""

        response = self._make_authenticated_request(
            'GET',
            '/api/v1/knowledge/popular?limit=10'
        )

        assert response.status_code == 200
        popular_questions = response.json()

        assert isinstance(popular_questions, list)

        # Should have popular questions (our test entries with votes)
        if popular_questions:
            for question in popular_questions:
                assert 'id' in question
                assert 'question' in question
                assert 'answer' in question
                assert 'upvotes' in question
                assert 'downvotes' in question
                assert 'created_at' in question

            # Should be ordered by popularity (upvotes - downvotes)
            if len(popular_questions) > 1:
                first_score = popular_questions[0]['upvotes'] - popular_questions[0]['downvotes']
                second_score = popular_questions[1]['upvotes'] - popular_questions[1]['downvotes']
                assert first_score >= second_score

        print(f"✅ Popular questions endpoint returned {len(popular_questions)} questions")

    def test_get_popular_questions_with_filters(self):
        """Test retrieving popular questions with filters."""

        # Test with crop type filter
        response = self._make_authenticated_request(
            'GET',
            '/api/v1/knowledge/popular?crop_type=rice&limit=5'
        )

        assert response.status_code == 200
        rice_popular = response.json()

        assert isinstance(rice_popular, list)

        # If results exist, they should be for rice
        for question in rice_popular:
            if question.get('crop_type'):
                assert question['crop_type'] == 'rice'

        # Test with category filter
        response = self._make_authenticated_request(
            'GET',
            '/api/v1/knowledge/popular?category=pest&limit=5'
        )

        assert response.status_code == 200
        pest_popular = response.json()

        assert isinstance(pest_popular, list)

        # If results exist, they should be in pest category
        for question in pest_popular:
            if question.get('category'):
                assert question['category'] == 'pest'

        # Test with language filter
        response = self._make_authenticated_request(
            'GET',
            '/api/v1/knowledge/popular?language=english&limit=5'
        )

        assert response.status_code == 200
        english_popular = response.json()

        assert isinstance(english_popular, list)

        # If results exist, they should be in English
        for question in english_popular:
            if question.get('language'):
                assert question['language'] == 'english'

        print("✅ Popular questions with filters work correctly")

    def test_delete_qa_entry(self):
        """Test deleting a Q&A entry."""
        
        # Use the Malayalam Q&A entry for deletion test
        response = self._make_authenticated_request(
            'DELETE',
            f'/api/v1/knowledge/{self.malayalam_qa_id}'
        )
        
        assert response.status_code == 200
        result = response.json()
        
        assert 'message' in result
        assert 'deleted successfully' in result['message']
        
        # Verify the entry is deleted
        response = self._make_authenticated_request(
            'GET',
            f'/api/v1/knowledge/{self.malayalam_qa_id}'
        )
        
        assert response.status_code == 404
    
    def test_search_with_short_query(self):
        """Test search with query that's too short."""
        
        response = self._make_authenticated_request(
            'GET',
            '/api/v1/knowledge/search?query=ab&limit=5'
        )
        
        assert response.status_code == 422  # Validation error for min_length
    
    def test_unauthorized_knowledge_access(self):
        """Test accessing knowledge endpoints without authentication."""
        
        # Test creating Q&A without auth
        qa_data = {
            "question": "Test question",
            "answer": "Test answer"
        }
        
        response = requests.post(
            f"{self.base_url}/api/v1/knowledge/",
            json=qa_data,
            timeout=self.timeout
        )
        
        assert response.status_code in [401, 403]
        
        # Test search without auth (should work as it's generally accessible)
        response = requests.get(
            f"{self.base_url}/api/v1/knowledge/search?query=test&limit=5",
            timeout=self.timeout
        )
        
        # Search might be accessible without auth, but other operations shouldn't be
        assert response.status_code in [200, 401, 403]


def test_knowledge_repository_endpoints():
    """Pytest entry point for knowledge repository tests."""
    
    test_class = TestKnowledgeRepositoryEndpoints()
    test_class.setup()
    
    # Run all tests in sequence
    test_methods = [
        test_class.test_create_qa_entry,
        test_class.test_create_multiple_qa_entries,
        test_class.test_get_qa_entries,
        test_class.test_get_qa_entries_filtered,
        test_class.test_get_specific_qa_entry,
        test_class.test_get_nonexistent_qa_entry,
        test_class.test_search_knowledge_vector_search,
        test_class.test_search_knowledge_traditional_search,
        test_class.test_search_knowledge_with_filters,
        test_class.test_update_qa_entry,
        test_class.test_vote_on_qa_entry,
        test_class.test_invalid_vote_type,
        test_class.test_ask_ai_question,
        test_class.test_get_categories_list,
        test_class.test_get_crops_list,
        test_class.test_get_popular_questions,
        test_class.test_get_popular_questions_with_filters,
        test_class.test_delete_qa_entry,
        test_class.test_search_with_short_query,
        test_class.test_unauthorized_knowledge_access
    ]
    
    for test_method in test_methods:
        try:
            test_method()
        except Exception as e:
            pytest.fail(f"Test {test_method.__name__} failed: {str(e)}")


if __name__ == "__main__":
    test_knowledge_repository_endpoints()