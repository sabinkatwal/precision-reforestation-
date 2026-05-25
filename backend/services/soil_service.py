from __future__ import annotations

from hashlib import sha256
from typing import Optional

import httpx

from backend.config.settings import get_settings
from backend.models.schemas import SoilData


def _noise(lat: float, lng: float, salt: str) -> float:
    digest = sha256(f"{lat:.6f}:{lng:.6f}:{salt}".encode()).hexdigest()
    return int(digest[:10], 16) / float(0xFFFFFFFFFF)


def _fallback_soil(lat: float, lng: float) -> SoilData:
    basin = 1.0 - abs(lat - 27.8) / 2.5
    moisture = max(0.1, min(1.0, 0.55 + basin * 0.18 + _noise(lat, lng, "moisture") * 0.12))
    ph = round(max(4.8, min(7.8, 5.2 + moisture * 1.9 + (_noise(lat, lng, "ph") - 0.5) * 0.7)), 2)
    nitrogen = round(max(0.03, min(0.24, 0.06 + moisture * 0.13 + (_noise(lat, lng, "nitrogen") - 0.5) * 0.03)), 3)
    clay = round(max(9.0, min(58.0, 21.0 + moisture * 18.0 + (_noise(lat, lng, "clay") - 0.5) * 12.0)), 2)
    organic_matter = round(max(1.1, min(12.0, 2.8 + moisture * 4.4 + (_noise(lat, lng, "om") - 0.5) * 1.4)), 2)
    return SoilData(
        ph=ph,
        nitrogen=nitrogen,
        clay=clay,
        organic_matter=organic_matter,
        source="deterministic-fallback",
    )


def _parse_layer(payload: dict, property_name: str) -> Optional[float]:
    """
    Parse the SoilGrids response structure:
    {
      "properties": {
        "layers": [
          {
            "name": "phh2o",
            "unit_measure": {"d_factor": 10, ...},
            "depths": [{"values": {"mean": 57}}]
          }
        ]
      }
    }
    """
    try:
        layers = payload["properties"]["layers"]
        for layer in layers:
            if layer["name"] == property_name:
                mean = layer["depths"][0]["values"]["mean"]
                d_factor = layer["unit_measure"].get("d_factor", 1)
                if mean is None:
                    return None
                return float(mean) / float(d_factor)
    except (KeyError, IndexError, TypeError):
        pass
    return None


async def _fetch_one(
    client: httpx.AsyncClient,
    lat: float,
    lng: float,
    property_name: str,
    settings,
) -> Optional[float]:
    """Fetch a single soil property from SoilGrids."""
    url = f"{settings.soilgrids_base_url}/properties/query"
    response = await client.get(
        url,
        params={
            "lat": lat,
            "lon": lng,
            "property": property_name,
            "depth": "0-5cm",
            "value": "mean",
        },
    )
    response.raise_for_status()
    return _parse_layer(response.json(), property_name)


async def _fetch_soilgrids(lat: float, lng: float) -> SoilData:
    import asyncio
    settings = get_settings()

    async with httpx.AsyncClient(timeout=settings.api_timeout_seconds) as client:
        ph_raw, nitrogen_raw, clay_raw, soc_raw = await asyncio.gather(
            _fetch_one(client, lat, lng, "phh2o", settings),
            _fetch_one(client, lat, lng, "nitrogen", settings),
            _fetch_one(client, lat, lng, "clay", settings),
            _fetch_one(client, lat, lng, "soc", settings),
        )

    if None in (ph_raw, nitrogen_raw, clay_raw, soc_raw):
        raise ValueError("Incomplete SoilGrids payload")

    # d_factor already applied in _parse_layer
    # SoilGrids SOC needs to be scaled down by 10 to match the usable value
    # expected by the rest of the app.
    return SoilData(
        ph=round(ph_raw, 2),
        nitrogen=round(nitrogen_raw, 3),
        clay=round(clay_raw, 2),
        organic_matter=round(soc_raw / 10.0, 2),
        source="soilgrids",
    )


async def fetch_soil(lat: float, lng: float) -> SoilData:
    # 1. SoilGrids (primary)
    try:
        return await _fetch_soilgrids(lat, lng)
    except Exception:
        pass

    # 2. Deterministic fallback
    return _fallback_soil(lat, lng)