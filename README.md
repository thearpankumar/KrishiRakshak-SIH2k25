# Digital Krishi Officer

<div align="center">

![Python](https://img.shields.io/badge/python-3.11+-3776ab?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)

**A comprehensive backend API solution for the Digital Krishi Officer mobile application, designed to empower farmers with AI-driven agricultural insights and community support.**

</div>

---

## N8n Workflow Architecture

<div align="center">

![n8n Workflow Architecture](docs/n8n.png)

*Advanced workflow automation integrating multiple data sources and AI services*

</div>

The system leverages **n8n** for sophisticated workflow automation, seamlessly integrating multiple data sources and AI services to provide farmers with real-time agricultural assistance, weather updates, and community-driven knowledge sharing.

---

## Features

### Core Capabilities
- **AI-Powered Chat Assistant** - Intelligent agricultural guidance using OpenAI integration
- **Image Analysis** - Advanced crop and pest identification through computer vision
- **Weather Integration** - Real-time weather data and agricultural advisories
- **Community Platform** - Farmer-to-farmer knowledge sharing and support
- **Location Services** - Geo-specific agricultural recommendations
- **Knowledge Base** - Comprehensive agricultural information repository

### Technical Features
- **FastAPI Backend** - High-performance async API framework
- **Vector Database** - Qdrant for semantic search and similarity matching
- **PostgreSQL Database** - Reliable data persistence with Alembic migrations
- **Redis Caching** - Performance optimization and session management
- **Rate Limiting** - API protection and resource management
- **File Upload System** - Secure handling of images and documents

## Technology Stack

<div align="center">

### Backend Framework
![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![Uvicorn](https://img.shields.io/badge/Uvicorn-2C5282?style=flat-square&logo=uvicorn&logoColor=white)

### Database & Storage
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=flat-square&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?style=flat-square&logo=redis&logoColor=white)
![Qdrant](https://img.shields.io/badge/Qdrant-24292E?style=flat-square&logo=qdrant&logoColor=white)

### AI & ML Integration
![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=flat-square&logo=openai&logoColor=white)
![Pillow](https://img.shields.io/badge/Pillow-3776AB?style=flat-square&logo=python&logoColor=white)

### DevOps & Deployment
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white)
![Docker Compose](https://img.shields.io/badge/Docker%20Compose-2496ED?style=flat-square&logo=docker&logoColor=white)
![n8n](https://img.shields.io/badge/n8n-EA4B71?style=flat-square&logo=n8n&logoColor=white)

</div>

## Quick Start

### Prerequisites
- Python 3.11 or higher
- Docker and Docker Compose
- PostgreSQL
- Redis

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd SIH-2025
   ```

2. **Environment Setup**
   ```bash
   cp .env.example .env
   # Configure your environment variables
   ```

3. **Docker Deployment**
   ```bash
   docker-compose up -d
   ```

4. **Local Development**
   ```bash
   # Create virtual environment
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate

   # Install dependencies
   pip install -e .

   # Run database migrations
   alembic upgrade head

   # Start the server
   uvicorn app.main:app --reload
   ```

## API Documentation

Once the server is running, access the interactive API documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Project Structure

```
SIH-2025/
├── app/
│   ├── api/                 # API route handlers
│   ├── core/                # Core configuration and utilities
│   ├── models/              # Database models
│   ├── services/            # Business logic services
│   └── utils/               # Utility functions
├── alembic/                 # Database migrations
├── tests/                   # Test suite
├── docs/                    # Documentation and assets
├── configs/                 # Configuration files
├── n8n-data/                # n8n workflow data
├── uploads/                 # File upload directory
├── docker-compose.yml       # Multi-service orchestration
├── pyproject.toml           # Project dependencies
├── .env.example             # Environment variables template
└── README.md                # Project documentation
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User authentication

### Core Services
- `POST /api/v1/chat/` - AI chat assistant
- `POST /api/v1/analysis/` - Image analysis
- `GET /api/v1/location/weather` - Weather data
- `GET /api/v1/community/` - Community posts
- `POST /api/v1/upload/` - File uploads

### n8n Integration
- `POST /api/v1/triggers/` - Workflow triggers
- `POST /api/v1/webhooks/` - Webhook handlers

## Testing

Run the comprehensive test suite:

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/
```

## Environment Variables

Key configuration variables (see `.env.example`):

```env
DATABASE_URL=postgresql://user:pass@localhost/dbname
REDIS_URL=redis://localhost:6379
OPENAI_API_KEY=your_openai_key
QDRANT_URL=http://localhost:6333
UPLOAD_DIR=./uploads
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support and questions, please contact the development team or create an issue in the repository.

---

**Digital Krishi Officer** - Empowering farmers through technology