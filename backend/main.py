from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config.settings import get_settings
from backend.routers.analysis import router as analysis_router
from backend.routers.elevation import router as elevation_router
from backend.routers.environment import router as environment_router
from backend.routers.soil import router as soil_router
from backend.routers.crops import router as crops_router

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered ecological restoration intelligence for Nepal.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(soil_router)
app.include_router(elevation_router)
app.include_router(environment_router)
app.include_router(analysis_router)
app.include_router(crops_router)


@app.get("/")
async def root() -> dict:
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "ok",
    }


@app.get("/health")
async def health() -> dict:
    return {"status": "healthy"}