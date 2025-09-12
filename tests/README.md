# Digital Krishi Officer API Tests

This directory contains comprehensive test suites for the Digital Krishi Officer FastAPI backend.

## Test Files

### `test_container_endpoints.py`
- **Main test suite** that validates all API endpoints
- Tests authentication, user management, farming profiles, and chat functionality
- Includes error handling and security testing
- Can be run standalone or with pytest
- Generates detailed test reports in JSON format

### `conftest.py`
- Pytest configuration and fixtures
- Database setup for integration tests
- Test data fixtures

### `run_tests.py`
- **Test runner script** for easy execution
- Supports waiting for container startup
- Configurable target URLs
- Executable script for CI/CD integration

## Running Tests

### Option 1: Direct Execution (Recommended)
```bash
# Run against local container
cd tests
uv run python test_container_endpoints.py

# Or use the test runner
uv run python run_tests.py --url http://localhost:8000 --wait
```

### Option 2: With pytest via uv
```bash
# Run all tests
uv run pytest tests/

# Run specific test file
uv run pytest tests/test_container_endpoints.py -v

# Run with detailed output
uv run pytest tests/test_container_endpoints.py -v -s
```

### Option 3: Container Testing
```bash
# Start your containers first
docker-compose up -d

# Wait for services and run tests
uv run python tests/run_tests.py --wait --timeout 120

# Or test against specific URL
uv run python tests/run_tests.py --url http://container-host:8000
```

## Test Coverage

The test suite covers:

### ✅ Health Endpoints
- `GET /` - Root endpoint
- `GET /health` - Health check

### ✅ Authentication Endpoints  
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `GET /api/v1/auth/me` - Get current user
- `PUT /api/v1/auth/me` - Update user profile
- `DELETE /api/v1/auth/me` - Delete user account (with cleanup)

### ✅ Farming Profile Endpoints
- `POST /api/v1/auth/profile` - Create farming profile
- `GET /api/v1/auth/profile` - Get farming profile  
- `PUT /api/v1/auth/profile` - Update farming profile
- `DELETE /api/v1/auth/profile` - Delete farming profile

### ✅ Chat/AI Endpoints
- `POST /api/v1/chat/` - Send chat message
- `GET /api/v1/chat/history` - Get chat history
- `GET /api/v1/chat/{message_id}` - Get specific message
- `DELETE /api/v1/chat/{message_id}` - Delete message
- `DELETE /api/v1/chat/history/clear` - Clear history

### ✅ Security Testing
- Unauthorized access attempts
- Invalid authentication
- Protected endpoint access

### ✅ Data Validation Testing  
- Invalid input data handling
- Malformed requests
- Edge cases

### ✅ Cleanup & Deletion Testing
- User account deletion with cascading cleanup
- Farming profile deletion
- Test data cleanup after test completion
- Database integrity after deletions

## Test Output

### Console Output
- Real-time test progress
- ✅/❌ Pass/fail indicators  
- Detailed error messages
- Test summary statistics

### JSON Report
- `test_results.json` - Comprehensive test results
- Timestamps for each test
- Response data and status codes
- Detailed failure information

## Environment Requirements

### For Container Testing:
- Docker and Docker Compose
- PostgreSQL container running
- Redis container running  
- FastAPI container running on port 8000

### For Local Testing:
- Python 3.11+
- All dependencies installed (`uv sync`)
- PostgreSQL running locally
- Redis running locally
- Environment variables configured

## Configuration

### Test Configuration (`TestConfig` class):
```python
BASE_URL = "http://localhost:8000"  # Change for different environments
TIMEOUT = 30  # Request timeout
TEST_USER = {...}  # Test user data
TEST_PROFILE = {...}  # Test farming profile data
```

### Environment Variables:
```bash
# For database testing (optional)
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/test_db
REDIS_URL=redis://localhost:6379/1
```

## CI/CD Integration

### GitHub Actions Example:
```yaml
- name: Run API Tests
  run: |
    uv run python tests/run_tests.py --wait --timeout 180
```

### Docker Compose Testing:
```yaml
version: '3.8'
services:
  api-tests:
    build: .
    command: uv run python tests/run_tests.py --url http://api:8000 --wait
    depends_on:
      - api
      - postgres
      - redis
```

## Troubleshooting

### Common Issues:

1. **Connection Refused**
   ```bash
   # Make sure containers are running
   docker-compose ps
   docker-compose logs api
   ```

2. **Database Errors**
   ```bash
   # Check database connectivity
   docker-compose logs postgres
   ```

3. **Authentication Failures**
   ```bash
   # Check if user registration/login is working
   # Verify JWT secret configuration
   ```

4. **Timeout Issues**
   ```bash
   # Increase timeout for slower environments
   uv run python run_tests.py --timeout 300
   ```

## Adding New Tests

To add new endpoint tests:

1. Add the endpoint test method to `DigitalKrishiTester` class
2. Update the `run_all_tests()` method to include new test
3. Add any required test data to `TestConfig`
4. Update this README with the new endpoint coverage

Example:
```python
def test_new_endpoint(self):
    """Test new API endpoint."""
    response = self.make_request('GET', '/api/v1/new-endpoint')
    data = self.assert_response(response, 200, "New endpoint test")
    assert "expected_field" in data
```