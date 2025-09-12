#!/bin/bash

# n8n Docker Compose Startup Script

set -e

echo "🚀 Starting n8n setup..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if docker compose is available (try new syntax first, then legacy)
if ! command -v docker > /dev/null 2>&1; then
    echo "❌ docker not found. Please install Docker."
    exit 1
fi

# Check for docker compose plugin first, then fallback to docker-compose
if docker compose version > /dev/null 2>&1; then
    DOCKER_COMPOSE_CMD="docker compose"
elif command -v docker-compose > /dev/null 2>&1; then
    DOCKER_COMPOSE_CMD="docker-compose"
else
    echo "❌ docker compose not found. Please install Docker Compose plugin."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your desired credentials and network settings"
    echo "   Default login: admin / changeme123"
fi

# Create directories if they don't exist
echo "📁 Creating necessary directories..."
mkdir -p n8n-data local-files

# Set proper permissions
echo "🔒 Setting directory permissions..."
chmod 755 n8n-data local-files

# Get server IP for network access
SERVER_IP=$(ip route get 8.8.8.8 | awk -F"src " 'NR==1{split($2,a," ");print a[1]}' 2>/dev/null || echo "localhost")

echo "🌐 Server details:"
echo "   Local access: http://localhost:5678"
echo "   Network access: http://${SERVER_IP}:5678"
echo "   Default credentials: admin / changeme123"

# Start services
echo "🐳 Starting Docker containers..."
${DOCKER_COMPOSE_CMD} up -d

# Wait a moment for services to start
sleep 5

# Check service status
echo "📊 Service status:"
${DOCKER_COMPOSE_CMD} ps

echo ""
echo "✅ n8n setup complete!"
echo ""
echo "🌐 Access n8n at:"
echo "   Local: http://localhost:5678"
echo "   Network: http://${SERVER_IP}:5678"
echo ""
echo "📝 To view logs: ${DOCKER_COMPOSE_CMD} logs -f n8n"
echo "🛑 To stop: ${DOCKER_COMPOSE_CMD} down"
echo ""
echo "⚠️  Remember to change default credentials in .env file for production use!"