from __future__ import annotations
import json
import re
import httpx
from backend.config.settings import get_settings
from backend.models.schemas import (
    ClimateData, CropAnalysisResult,
    CropSuggestion, ElevationData, SoilData,
)

CROP_PROMPT = """You are an agricultural expert for Nepal and South Asia.

Analyze this land patch and recommend the best crops:

Location Data:
- Elevation: {elevation}m
- Slope: {slope}°

Soil Data:
- pH: {ph}
- Nitrogen: {nitrogen} g/kg
- Clay: {clay}%
- Organic Matter: {organic_matter}%

Climate Data:
- Avg Max Temp: {avg_temp_max}°C
- Avg Min Temp: {avg_temp_min}°C
- Annual Rainfall: {annual_rainfall}mm
- Dry Months: {dry_months}

Return STRICT JSON only:
{{
  "crops": [
    {{
      "name": string,
      "local_name": string (Nepali name),
      "confidence": number (0-100),
      "season": "Kharif | Rabi | Year-round",
      "planting_month": string,
      "harvest_month": string,
      "water_requirement": "Low | Medium | High",
      "soil_suitability": string,
      "yield_estimate": string,
      "reason": string,
      "warnings": [string]
    }}
  ],
  "best_season": string,
  "irrigation_needed": boolean,
  "insight": string
}}

Return top 5 crops. Consider Nepal's agricultural zones:
- Terai (<300m): Rice, Wheat, Maize, Sugarcane, Lentils
- Mid-hills (300-2000m): Maize, Millet, Potato, Vegetables
- High-hills (>2000m): Potato, Buckwheat, Barley, Apple
"""


def _fallback_crops(
    soil: SoilData,
    elevation: ElevationData,
    climate: ClimateData,
) -> CropAnalysisResult:
    elev = elevation.elevation
    rainfall = climate.annual_rainfall

    if elev < 300:
        crops = [
            CropSuggestion(name="Rice", local_name="Dhan", confidence=90,
                season="Kharif", planting_month="June", harvest_month="November",
                water_requirement="High", soil_suitability="Clay loam soils",
                yield_estimate="3-4 tons/hectare", warnings=["Needs irrigation in dry years"],
                reason="Ideal for Terai lowlands with high rainfall and flat terrain."),
            CropSuggestion(name="Wheat", local_name="Gahu", confidence=85,
                season="Rabi", planting_month="November", harvest_month="March",
                water_requirement="Medium", soil_suitability="Well-drained loam",
                yield_estimate="2.5-3.5 tons/hectare", warnings=[],
                reason="Excellent winter crop for Terai plains after rice harvest."),
            CropSuggestion(name="Lentil", local_name="Masuro", confidence=78,
                season="Rabi", planting_month="October", harvest_month="February",
                water_requirement="Low", soil_suitability="Sandy loam",
                yield_estimate="0.8-1.2 tons/hectare", warnings=[],
                reason="Nitrogen-fixing legume ideal for crop rotation."),
        ]
    elif elev < 2000:
        crops = [
            CropSuggestion(name="Maize", local_name="Makai", confidence=88,
                season="Kharif", planting_month="March", harvest_month="August",
                water_requirement="Medium", soil_suitability="Well-drained loam",
                yield_estimate="2-3 tons/hectare", warnings=["Vulnerable to waterlogging"],
                reason="Most versatile mid-hill crop with strong market demand."),
            CropSuggestion(name="Potato", local_name="Alu", confidence=85,
                season="Rabi", planting_month="October", harvest_month="February",
                water_requirement="Medium", soil_suitability="Sandy loam, acidic OK",
                yield_estimate="15-20 tons/hectare", warnings=["Late blight risk in wet seasons"],
                reason="High-value crop well suited to mid-hill cool conditions."),
            CropSuggestion(name="Millet", local_name="Kodo", confidence=80,
                season="Kharif", planting_month="May", harvest_month="October",
                water_requirement="Low", soil_suitability="Poor soils tolerated",
                yield_estimate="1-1.5 tons/hectare", warnings=[],
                reason="Drought-tolerant staple that grows on marginal hillside soils."),
        ]
    else:
        crops = [
            CropSuggestion(name="Potato", local_name="Alu", confidence=92,
                season="Year-round", planting_month="March", harvest_month="August",
                water_requirement="Medium", soil_suitability="Well-drained, acidic",
                yield_estimate="20-25 tons/hectare", warnings=["Frost risk above 3500m"],
                reason="Best high-altitude cash crop with excellent yields in cool conditions."),
            CropSuggestion(name="Buckwheat", local_name="Phapar", confidence=83,
                season="Kharif", planting_month="June", harvest_month="September",
                water_requirement="Low", soil_suitability="Poor soils tolerated",
                yield_estimate="0.8-1.2 tons/hectare", warnings=[],
                reason="Traditional high-altitude crop, frost hardy and nutritious."),
            CropSuggestion(name="Barley", local_name="Jau", confidence=78,
                season="Rabi", planting_month="October", harvest_month="April",
                water_requirement="Low", soil_suitability="Well-drained",
                yield_estimate="1.5-2 tons/hectare", warnings=[],
                reason="Cold-tolerant cereal suited for high-elevation dry conditions."),
        ]

    irrigation_needed = climate.annual_rainfall < 1000 or climate.dry_months > 5
    return CropAnalysisResult(
        crops=crops,
        best_season="Kharif (June-November)" if climate.annual_rainfall > 1000 else "Rabi (October-March)",
        irrigation_needed=irrigation_needed,
        insight=f"At {elev:.0f}m elevation with {climate.annual_rainfall:.0f}mm annual rainfall, "
                f"this site suits {'lowland staples' if elev < 300 else 'mid-hill mixed cropping' if elev < 2000 else 'high-value mountain crops'}.",
        climate=climate,
        soil=soil,
        elevation=elevation,
    )


async def analyze_crops(
    soil: SoilData,
    elevation: ElevationData,
    climate: ClimateData,
    slope: float,
) -> CropAnalysisResult:
    settings = get_settings()
    if not settings.anthropic_api_key:
        return _fallback_crops(soil, elevation, climate)

    prompt = CROP_PROMPT.format(
        elevation=round(elevation.elevation, 1),
        slope=round(slope, 1),
        ph=round(soil.ph, 2),
        nitrogen=round(soil.nitrogen, 3),
        clay=round(soil.clay, 2),
        organic_matter=round(soil.organic_matter, 2),
        avg_temp_max=climate.avg_temp_max,
        avg_temp_min=climate.avg_temp_min,
        annual_rainfall=climate.annual_rainfall,
        dry_months=climate.dry_months,
    )

    headers = {
        "x-api-key": settings.anthropic_api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": settings.anthropic_model,
        "max_tokens": 1200,
        "temperature": 0.2,
        "messages": [{"role": "user", "content": prompt}],
    }

    try:
        async with httpx.AsyncClient(timeout=settings.api_timeout_seconds) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            text = "".join(
                block.get("text", "")
                for block in data.get("content", [])
                if isinstance(block, dict)
            )
            text = text.strip()
            if text.startswith("```"):
                text = re.sub(r"^```(?:json)?\s*", "", text, re.IGNORECASE)
                text = re.sub(r"\s*```$", "", text)
            start, end = text.find("{"), text.rfind("}")
            raw = json.loads(text[start:end + 1])

            return CropAnalysisResult(
                crops=[CropSuggestion(**c) for c in raw["crops"][:5]],
                best_season=raw["best_season"],
                irrigation_needed=raw["irrigation_needed"],
                insight=raw["insight"],
                climate=climate,
                soil=soil,
                elevation=elevation,
            )
    except Exception:
        return _fallback_crops(soil, elevation, climate)