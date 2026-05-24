from __future__ import annotations

from typing import List

from backend.models.schemas import ElevationData

from backend.services.narc_service import fetch_narc_elevation, fetch_narc_neighbor_elevations


async def fetch_elevation(lat: float, lng: float) -> ElevationData:
    return await fetch_narc_elevation(lat, lng)


async def fetch_neighbor_elevations(lat: float, lng: float, step_degrees: float = 0.01) -> List[float]:
    return await fetch_narc_neighbor_elevations(lat, lng, step_degrees=step_degrees)
