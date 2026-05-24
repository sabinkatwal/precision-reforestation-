from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from backend.models.schemas import EnvironmentData
from backend.services.elevation_service import fetch_elevation, fetch_neighbor_elevations
from backend.services.soil_service import fetch_soil
from backend.utils.ndvi import generate_ndvi
from backend.utils.slope import estimate_slope, terrain_class_from_slope

router = APIRouter(prefix="/environment", tags=["environment"])


@router.get("", response_model=EnvironmentData)
async def get_environment(lat: float = Query(..., ge=-90, le=90), lng: float = Query(..., ge=-180, le=180)) -> EnvironmentData:
    try:
        soil = await fetch_soil(lat, lng)
        elevation = await fetch_elevation(lat, lng)
        neighbors = await fetch_neighbor_elevations(lat, lng)
        north, south, east, west = (neighbors + [None, None, None, None])[:4]
        slope = estimate_slope(
            center_elevation=elevation.elevation,
            north=north,
            south=south,
            east=east,
            west=west,
            lat=lat,
        )
        ndvi = generate_ndvi(lat, lng, elevation.elevation, soil.ph, soil.nitrogen, soil.clay, soil.organic_matter)
        return EnvironmentData(
            lat=lat,
            lng=lng,
            soil=soil,
            elevation=elevation,
            ndvi=ndvi,
            slope=slope,
            terrain_class=terrain_class_from_slope(slope),
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
