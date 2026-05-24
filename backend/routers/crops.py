from __future__ import annotations

import asyncio
from fastapi import APIRouter, Query
from backend.models.schemas import CropAnalysisResult
from backend.services.climate_service import fetch_climate
from backend.services.elevation_service import fetch_elevation, fetch_neighbor_elevations
from backend.services.soil_service import fetch_soil
from backend.services.crop_service import analyze_crops
from backend.utils.slope import estimate_slope

router = APIRouter(prefix="/crops", tags=["crops"])


@router.get("", response_model=CropAnalysisResult)
async def get_crop_recommendations(
    lat: float = Query(..., ge=26.0, le=30.5),
    lng: float = Query(..., ge=80.0, le=88.5),
) -> CropAnalysisResult:
    soil, elevation, climate = await asyncio.gather(
        fetch_soil(lat, lng),
        fetch_elevation(lat, lng),
        fetch_climate(lat, lng),
    )
    neighbors = await fetch_neighbor_elevations(lat, lng)
    slope = estimate_slope(
        center_elevation=elevation.elevation,
        north=neighbors[0],
        south=neighbors[1],
        east=neighbors[2],
        west=neighbors[3],
        lat=lat,
    )
    return await analyze_crops(soil, elevation, climate, slope)