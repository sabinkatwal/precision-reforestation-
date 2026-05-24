from __future__ import annotations

import asyncio
import re
from typing import Any, Dict, Iterable, List, Optional

import httpx
from fastapi import HTTPException

from backend.config.settings import get_settings
from backend.models.schemas import ElevationData, SoilData


def _extract_numeric(value: Any) -> Optional[float]:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        match = re.search(r"-?\d+(?:\.\d+)?", value.replace(",", ""))
        if match:
            return float(match.group(0))
        return None
    if isinstance(value, dict):
        for key in ("value", "mean", "val", "median", "ph", "organic_matter", "total_nitrogen", "clay", "elevation"):
            candidate = value.get(key)
            if candidate is not None:
                extracted = _extract_numeric(candidate)
                if extracted is not None:
                    return extracted
        for nested in value.values():
            extracted = _extract_numeric(nested)
            if extracted is not None:
                return extracted
    if isinstance(value, list):
        for item in value:
            extracted = _extract_numeric(item)
            if extracted is not None:
                return extracted
    return None


def _normalize_payload_key(payload: Dict[str, Any], candidates: Iterable[str]) -> Any:
    lowered = {str(key).lower(): value for key, value in payload.items()}
    for candidate in candidates:
        candidate_key = candidate.lower()
        if candidate_key in lowered:
            return lowered[candidate_key]
    return None


async def fetch_narc_profile(lat: float, lng: float) -> Dict[str, Any]:
    settings = get_settings()
    timeout = httpx.Timeout(settings.api_timeout_seconds)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(settings.narc_soil_api_url, params={"lat": lat, "lon": lng})
            response.raise_for_status()
            payload = response.json()
            if isinstance(payload, list):
                payload = next((item for item in payload if isinstance(item, dict)), None)
            elif isinstance(payload, dict) and isinstance(payload.get("results"), list):
                payload = next((item for item in payload["results"] if isinstance(item, dict)), None)
            if not isinstance(payload, dict):
                raise ValueError("Unexpected NARC response shape")
            return payload
    except asyncio.CancelledError as exc:
        raise HTTPException(status_code=504, detail="NARC request cancelled or timed out") from exc
    except httpx.TimeoutException as exc:
        raise HTTPException(status_code=504, detail="NARC request timed out") from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"NARC API returned {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail="Unable to reach NARC API") from exc


def _first_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    if isinstance(payload, dict) and isinstance(payload.get("results"), list):
        first_item = next((item for item in payload["results"] if isinstance(item, dict)), None)
        if first_item is not None:
            return first_item
    return payload


def _soil_from_profile(payload: Dict[str, Any], lat: float, lng: float) -> SoilData:
    payload = _first_payload(payload)
    ph = _extract_numeric(_normalize_payload_key(payload, ("ph", "phh2o", "Ph")))
    organic_matter = _extract_numeric(_normalize_payload_key(payload, ("organic_matter", "organic matter", "Organic_matter")))
    nitrogen = _extract_numeric(_normalize_payload_key(payload, ("total_nitrogen", "nitrogen", "Total_nitrogen")))
    clay = _extract_numeric(_normalize_payload_key(payload, ("clay", "Clay")))
    if None in (ph, organic_matter, nitrogen, clay):
        raise ValueError("Incomplete NARC soil payload")
    return SoilData(
        ph=round(float(ph), 2),
        nitrogen=round(float(nitrogen), 3),
        clay=round(float(clay), 2),
        organic_matter=round(float(organic_matter), 2),
        source="narc",
    )


def _elevation_from_profile(payload: Dict[str, Any], lat: float, lng: float) -> ElevationData:
    payload = _first_payload(payload)
    coord = payload.get("coord") or {}
    elevation = _extract_numeric(coord.get("elevation"))
    if elevation is None:
        raise ValueError("NARC elevation missing from payload")
    return ElevationData(elevation=round(float(elevation), 2), source="narc")


async def fetch_narc_soil(lat: float, lng: float) -> SoilData:
    payload = await fetch_narc_profile(lat, lng)
    return _soil_from_profile(payload, lat, lng)


async def fetch_narc_elevation(lat: float, lng: float) -> ElevationData:
    payload = await fetch_narc_profile(lat, lng)
    return _elevation_from_profile(payload, lat, lng)


async def fetch_narc_neighbor_elevations(lat: float, lng: float, step_degrees: float = 0.01) -> List[Optional[float]]:
    offsets = (
        (lat + step_degrees, lng),
        (lat - step_degrees, lng),
        (lat, lng + step_degrees),
        (lat, lng - step_degrees),
    )
    probe_steps = (step_degrees, step_degrees / 2.0, step_degrees / 4.0, step_degrees / 8.0)
    values: List[Optional[float]] = []

    for sample_lat, sample_lng in offsets:
        sample_elevation: Optional[float] = None
        for probe_step in probe_steps:
            probe_lat = lat + (sample_lat - lat) * (probe_step / step_degrees)
            probe_lng = lng + (sample_lng - lng) * (probe_step / step_degrees)
            try:
                elevation = await fetch_narc_elevation(probe_lat, probe_lng)
                sample_elevation = elevation.elevation
                break
            except Exception as exc:
                continue
        values.append(sample_elevation)

    return values