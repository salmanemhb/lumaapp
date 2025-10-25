"""
Main FastAPI application
Version: 1.0.1 - Fixed pandas import issues
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from app.config import settings
from app.routes import auth, files, dashboard, reports, agents
from agents.data_intake_agent import router as agent1_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Luma ESG API",
    description="Backend API for Luma ESG automation platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(files.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(agents.router, prefix="/api")  # n8n agent endpoints

# Agent routers
app.include_router(agent1_router)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    logger.info("🚀 Starting Luma ESG API...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Allowed origins: {settings.allowed_origins_list}")
    logger.info(f"RESEND_API_KEY configured: {settings.RESEND_API_KEY[:10]}..." if settings.RESEND_API_KEY else "❌ RESEND_API_KEY NOT SET")
    logger.info(f"Admin Email: {settings.ADMIN_EMAIL}")
    logger.info(f"Google Form URL: {settings.GOOGLE_FORM_URL}")
    logger.info("✅ Database connection ready")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Luma ESG API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "timestamp": "2025-10-22"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
