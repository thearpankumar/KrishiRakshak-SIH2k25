# Digital Krishi Officer API Tests

Comprehensive test suite for all Digital Krishi Officer API endpoints.

## Quick Start

```bash
# Make sure containers are running
docker-compose up -d

# Run all tests
cd tests/
./test.sh
```

## Test Suites

| **Suite** | **File** | **Coverage** |
|-----------|----------|-------------|
| **Core** | `test_container_endpoints.py` | Auth, Chat, Profiles |
| **Analysis** | `test_analysis_endpoints.py` | Image Upload, AI Vision |
| **Knowledge** | `test_knowledge_endpoints.py` | Q&A, Vector Search |
| **Community** | `test_community_endpoints.py` | Groups, Messaging |
| **Location** | `test_location_endpoints.py` | Retailers, Geospatial |

## Run Options

```bash
# All tests (recommended)
./test.sh

# With pytest
./test.sh --pytest

# Individual suites
uv run pytest tests/test_analysis_endpoints.py -v
uv run pytest tests/test_knowledge_endpoints.py -v
uv run pytest tests/test_community_endpoints.py -v
uv run pytest tests/test_location_endpoints.py -v

# Comprehensive runner
uv run python run_all_tests.py
```

## Test Coverage

✅ **100+ API endpoints tested**
- Authentication & Authorization
- AI-Powered Chat System  
- Image Analysis & Vision AI
- Knowledge Repository with Vector Search
- Community Group Chats
- Location-Based Services
- Error Handling & Security

## Requirements

- Docker containers running (`docker-compose up -d`)
- Services accessible:
  - FastAPI: `http://localhost:8000`
  - Qdrant: `http://localhost:6333`
  - PostgreSQL: `localhost:5432`
  - Redis: `localhost:6379`

## Output

- Console: Real-time test progress
- Files: `test_results.json`, `comprehensive_test_results.json`

## Troubleshooting

```bash
# Check containers
docker ps

# Check API health
curl http://localhost:8000/health

# View logs
docker logs krishi-fastapi
```