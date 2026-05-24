from __future__ import annotations

import httpx
from backend.models.schemas import ClimateData


def _fallback_climate(lat: float, lng: float) -> ClimateData:
    base_temp = 25 - (lat - 26.5) * 2
    return ClimateData(
        avg_temp_max=round(base_temp, 1),
        avg_temp_min=round(base_temp - 12, 1),
        annual_rainfall=1400.0,
        dry_months=4,
        source="deterministic-fallback",
    )


async def fetch_climate(lat: float, lng: float) -> ClimateData:
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lng,
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
        ],
        "timezone": "Asia/Kathmandu",
        "forecast_days": 92,
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            daily = data.get("daily", {})

            temps_max = daily.get("temperature_2m_max", [])
            temps_min = daily.get("temperature_2m_min", [])
            rainfall = daily.get("precipitation_sum", [])

            avg_max = round(sum(temps_max) / len(temps_max), 1) if temps_max else 25.0
            avg_min = round(sum(temps_min) / len(temps_min), 1) if temps_min else 13.0
            annual_rainfall = round(sum(rainfall) * 4, 1) if rainfall else 1400.0
            dry_months = sum(1 for r in rainfall if r < 20) // 3

            return ClimateData(
                avg_temp_max=avg_max,
                avg_temp_min=avg_min,
                annual_rainfall=annual_rainfall,
                dry_months=dry_months,
                source="open-meteo",
            )
    except Exception:
        return _fallback_climate(lat, lng)