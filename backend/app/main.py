import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.errors import NeuroScanError
from app.api.routes import router as api_router
from app.ml.inference import inference_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"==================================================")
    print(f"[*] {settings.PROJECT_NAME} v{settings.VERSION} Starting Up")
    print(f"[*] Storage directory: {settings.STORAGE_DIR}")
    print(f"[*] Model status: {'LOADED' if inference_service.is_loaded else 'CHECKPOINT UNAVAILABLE'}")
    print(f"[*] Compute device: {inference_service.device}")
    print(f"[*] Research Disclaimer: {settings.RESEARCH_DISCLAIMER[:80]}...")
    print(f"==================================================")
    yield
    print(f"[*] {settings.PROJECT_NAME} shutting down cleanly.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(NeuroScanError)
async def neuroscan_error_handler(request: Request, exc: NeuroScanError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "error_type": exc.__class__.__name__}
    )

# Mount API routes
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "documentation": "/docs",
        "api_prefix": settings.API_V1_STR,
        "model_loaded": inference_service.is_loaded,
        "notice": settings.RESEARCH_DISCLAIMER
    }
