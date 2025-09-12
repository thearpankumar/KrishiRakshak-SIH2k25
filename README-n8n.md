# Digital Krishi Officer - Backend Setup

This setup provides a complete Digital Krishi Officer backend with n8n automation platform, FastAPI backend, PostgreSQL database, Redis caching, and Qdrant vector database.

## Services Included

- **FastAPI**: Main backend API server with AI chat, authentication, and analysis
- **n8n**: Automation platform for workflows (scheduler, alerts, integrations)
- **PostgreSQL**: Robust database for production use (with auto-creation of krishi_officer database)
- **Redis**: Caching and queue management for FastAPI and n8n
- **Qdrant**: Vector database for semantic search in Q&A system

## Quick Start

1. **Prepare environment file**:
   ```bash
   cp .env.example .env
   # Edit .env file with your desired credentials, OpenAI API key, and network settings
   ```

2. **Install Python dependencies** (for FastAPI development):
   ```bash
   # Install uv if not already installed
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Install project dependencies
   uv sync
   ```

3. **Start the services**:
   ```bash
   # Start all services (PostgreSQL, Redis, Qdrant, n8n, FastAPI)
   docker-compose up -d
   
   # View logs for all services
   docker-compose logs -f
   ```

4. **Run database migrations**:
   ```bash
   # Run Alembic migrations to create database schema
   uv run alembic upgrade head
   ```

5. **Access the services**:
   - **FastAPI Backend**: http://localhost:8000
     - API Documentation: http://localhost:8000/docs
     - Health Check: http://localhost:8000/health
   - **n8n Workflows**: http://localhost:5678
     - Login with credentials from .env file (default: admin/changeme123)
   - **Qdrant Vector DB**: http://localhost:6333/dashboard

## Network Configuration

### For Local Network Access

1. Find your server's IP address:
   ```bash
   ip addr show | grep inet
   ```

2. Update the WEBHOOK_URL in .env file:
   ```
   WEBHOOK_URL=http://192.168.1.100:5678/
   ```

3. Access n8n from other devices: `http://192.168.1.100:5678`

## Directory Structure

```
├── app/                    # FastAPI application
│   ├── api/               # API route handlers
│   ├── core/              # Core functionality (config, security, database)
│   ├── models/            # Database models and Pydantic schemas
│   ├── services/          # Business logic services
│   └── utils/             # Utility functions
├── alembic/               # Database migrations
│   ├── versions/          # Migration files
│   └── env.py            # Alembic configuration
├── tests/                 # Unit tests
├── uploads/               # File upload directory (auto-created)
├── docker-compose.yml     # Main compose file
├── Dockerfile             # FastAPI container build
├── pyproject.toml         # Python project configuration
├── init-db.sh            # Database initialization script
├── .env                   # Environment configuration
├── .env.example          # Environment template
├── .gitignore            # Git ignore rules
└── README-n8n.md         # This file
```

## Security Notes

⚠️ **Important**: Change default passwords and add API keys in .env file before use!

### Required Configuration:
- **OPENAI_API_KEY**: Required for AI chat functionality
- **SECRET_KEY**: Change to a long, random string for JWT security
- **N8N_BASIC_AUTH_PASSWORD**: Change default n8n login password
- **DB_POSTGRES_PASSWORD**: Change default database password
- **REDIS_PASSWORD**: Change default Redis password

### API Endpoints:
- **Authentication**: `/api/v1/auth/register`, `/api/v1/auth/login`
- **Chat**: `/api/v1/chat/` (POST for sending messages)
- **User Profile**: `/api/v1/auth/me`, `/api/v1/auth/profile`
- **API Documentation**: `/docs` (Swagger UI)

## Development Commands

### FastAPI Development
```bash
# Run FastAPI locally (for development)
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run database migrations
uv run alembic upgrade head

# Create new migration after model changes
uv run alembic revision --autogenerate -m "Description of changes"

# Rollback last migration
uv run alembic downgrade -1

# Check migration history
uv run alembic history

# Run tests
uv run pytest

# Install new package
uv add package-name

# Remove package
uv remove package-name
```

### Docker Commands
```bash
# Start all services
docker-compose up -d

# View logs for specific service
docker-compose logs -f fastapi
docker-compose logs -f postgres
docker-compose logs -f n8n
docker-compose logs -f qdrant

# Stop services
docker-compose down

# Restart specific service
docker-compose restart fastapi

# Rebuild and start
docker-compose up --build -d

# Update to latest versions
docker-compose pull && docker-compose up -d
```

### Database Commands
```bash
# Connect to PostgreSQL database
docker exec -it n8n-postgres psql -U n8n -d krishi_officer

# Backup database
docker exec n8n-postgres pg_dump -U n8n krishi_officer > backup.sql

# Restore database
docker exec -i n8n-postgres psql -U n8n krishi_officer < backup.sql

# Reset database (WARNING: destroys all data)
docker-compose down
docker volume rm sih-2025_postgres_data
docker-compose up -d postgres
# Wait for postgres to be ready, then run migrations
uv run alembic upgrade head
```

## Troubleshooting

### Can't access from network
1. Check firewall settings: `sudo ufw status`
2. Verify n8n is binding to 0.0.0.0: check container logs
3. Ensure WEBHOOK_URL matches your server IP

### Database connection issues
1. Check PostgreSQL container status: `docker-compose logs postgres`
2. Verify database credentials in .env file

### Performance optimization
- Increase Docker resources if needed
- Consider using external PostgreSQL for production
- Monitor container resource usage: `docker stats`

## File Operations

The `local-files/` directory is mounted to `/files` in the n8n container. Use this path in n8n's "Read/Write Files from Disk" nodes.

## External Libraries

The setup allows common libraries (axios, lodash, moment). Add more in docker-compose.yml under `NODE_FUNCTION_ALLOW_EXTERNAL`.

## Production Considerations

- Use strong passwords
- Set up SSL/TLS with reverse proxy (Traefik/Nginx)
- Regular backups
- Monitor resource usage
- Consider using managed database services