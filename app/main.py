from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import redis.asyncio as redis
from contextlib import asynccontextmanager
import os

from .core.config import settings
from .core.database import create_tables, Session, engine
from .services.vector_service import vector_service


# Create upload directory early
os.makedirs(settings.upload_dir, exist_ok=True)

# Create limiter instance
limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    await create_tables()
    
    # Initialize Redis connection
    app.state.redis = redis.from_url(settings.redis_url)
    
    # Initialize Vector Database
    try:
        await vector_service.initialize()
        print("✅ Vector database initialized successfully")
    except Exception as e:
        print(f"⚠️  Vector database initialization failed: {e}")
    
    yield
    
    # Shutdown
    await app.state.redis.close()

# Create FastAPI app
app = FastAPI(
    title="Digital Krishi Officer API",
    description="Backend API for the Digital Krishi Officer mobile application",
    version="1.0.0",
    lifespan=lifespan
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Mount static files for uploads
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

# Include routers
from .api import auth, chat, analysis, community, location, knowledge, upload, triggers, webhooks
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["analysis"])
app.include_router(community.router, prefix="/api/v1/community", tags=["community"])
app.include_router(location.router, prefix="/api/v1/location", tags=["location"])
app.include_router(knowledge.router, prefix="/api/v1/knowledge", tags=["knowledge"])
app.include_router(upload.router, prefix="/api/v1/upload", tags=["upload"])
app.include_router(triggers.router, prefix="/api/v1/triggers", tags=["n8n-triggers"])
app.include_router(webhooks.router, prefix="/api/v1/webhooks", tags=["n8n-webhooks"])

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Digital Krishi Officer API", "status": "running"}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "digital-krishi-officer-api"}