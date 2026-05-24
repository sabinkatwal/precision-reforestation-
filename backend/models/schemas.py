from __future__ import annotations

from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class Coordinates(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)


class SoilData(BaseModel):
    ph: float
    nitrogen: float
    clay: float
    organic_matter: float
    source: str = "soilgrids"


class ElevationData(BaseModel):
    elevation: float
    source: str = "open-elevation"


class EnvironmentData(BaseModel):
    lat: float
    lng: float
    soil: SoilData
    elevation: ElevationData
    ndvi: float
    slope: float
    terrain_class: str


class SpeciesSuggestion(BaseModel):
    name: str
    confidence: float = Field(..., ge=0, le=100)
    reason: str


class AnalysisResult(BaseModel):
    biodiversity_score: float = Field(..., ge=0, le=100)
    erosion_risk: Literal["Low", "Medium", "High"]
    carbon_potential: float
    species: List[SpeciesSuggestion]
    insight: str
    environment: EnvironmentData


class AnalysisRequest(Coordinates):
    pass


class ErrorResponse(BaseModel):
    detail: str
    context: Optional[dict] = None


# ── Crop Recommendation Models ─────────────────────────────────────────────

class ClimateData(BaseModel):
    avg_temp_max: float
    avg_temp_min: float
    annual_rainfall: float
    dry_months: int
    source: str = "open-meteo"


class CropSuggestion(BaseModel):
    name: str
    local_name: str
    confidence: float = Field(..., ge=0, le=100)
    season: Literal["Kharif", "Rabi", "Year-round"]
    planting_month: str
    harvest_month: str
    water_requirement: Literal["Low", "Medium", "High"]
    soil_suitability: str
    yield_estimate: str
    reason: str
    warnings: List[str] = []


class CropAnalysisResult(BaseModel):
    crops: List[CropSuggestion]
    best_season: str
    irrigation_needed: bool
    insight: str
    climate: ClimateData
    soil: SoilData
    elevation: ElevationData


class CropRequest(Coordinates):
    pass