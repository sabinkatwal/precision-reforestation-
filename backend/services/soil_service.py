from __future__ import annotations

from backend.models.schemas import SoilData

from backend.services.narc_service import fetch_narc_soil


async def fetch_soil(lat: float, lng: float) -> SoilData:
    return await fetch_narc_soil(lat, lng)
