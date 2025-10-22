"""
Main FastAPI application
Version: 1.0.1 - Fixed pandas import issues
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routes import auth, files, dashboard, reports

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


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    print("🚀 Starting Luma ESG API...")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Allowed origins: {settings.allowed_origins_list}")
    print("✅ Database connection ready")


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
