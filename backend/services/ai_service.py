from __future__ import annotations

import json
import re
from typing import Any, Dict, List

import httpx

from backend.config.settings import get_settings
from backend.models.schemas import AnalysisResult, EnvironmentData, SpeciesSuggestion


PROMPT_TEMPLATE = """You are an ecological restoration expert specializing in Himalayan ecosystems.

Analyze this land patch in Nepal:

Elevation: {elevation} meters  
Slope: {slope} degrees  
NDVI: {ndvi}  

Soil:
- pH: {ph}
- Nitrogen: {nitrogen}
- Clay: {clay}%
- Organic Matter: {organic_matter}%

Return STRICT JSON:

{
  "biodiversity_score": number (0-100),
  "erosion_risk": "Low | Medium | High",
  "carbon_potential": number (tons/year),
  "species": [
    {
      "name": string,
      "confidence": number (0-100),
      "reason": string
    }
  ],
  "insight": string
}
"""


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def _species_from_environment(environment: EnvironmentData) -> List[SpeciesSuggestion]:
    elevation = environment.elevation.elevation
    slope = environment.slope
    ndvi = environment.ndvi
    soil = environment.soil
    species: List[SpeciesSuggestion] = []

    if elevation < 900:
        species.append(SpeciesSuggestion(name="Shorea robusta(Sal)", confidence=84, reason="Low-elevation Terai conditions with warm temperatures and fertile soils."))
        species.append(SpeciesSuggestion(name="Dalbergia sissoo(Sisau)", confidence=79, reason="Supports degraded riverine and lowland restoration where moisture is available."))
    elif elevation < 1800:
        species.append(SpeciesSuggestion(name="Pinus roxburghii(Khote Sallo)", confidence=88, reason="Strong fit for mid-elevation Himalayan slopes with moderate disturbance."))
        species.append(SpeciesSuggestion(name="Alnus nepalensis(Utis)", confidence=82, reason="Nitrogen-fixing pioneer that stabilizes landslide-prone hillsides."))
    else:
        species.append(SpeciesSuggestion(name="Quercus lanata(Banjh)", confidence=86, reason="Well adapted to cooler montane forests with robust carbon storage potential."))
        species.append(SpeciesSuggestion(name="Rhododendron arboreum(Lali Gurans)", confidence=80, reason="Native highland broadleaf species suited to acidic, cooler sites."))

    if ndvi > 0.45 and soil.organic_matter > 4:
        species.append(SpeciesSuggestion(name="Schima wallichii(Chilaune)", confidence=76, reason="Performs well where canopy recovery and mixed broadleaf structure are already emerging."))
    elif slope > 20:
        species.append(SpeciesSuggestion(name="Bambusa nutans(Mal Bans)", confidence=74, reason="Useful for rapid slope binding and soil reinforcement on steeper terrain."))
    else:
        species.append(SpeciesSuggestion(name="Celtis australis(Khari)", confidence=72, reason="Versatile native tree that supports multi-strata restoration on moderately stable ground."))

    return species[:3]


def _strip_json(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]
    return text


async def _call_claude(prompt: str) -> Dict[str, Any]:
    settings = get_settings()
    if not settings.anthropic_api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not configured")

    headers = {
        "x-api-key": settings.anthropic_api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": settings.anthropic_model,
        "max_tokens": 900,
        "temperature": 0.2,
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
    }
    timeout = httpx.Timeout(settings.api_timeout_seconds)
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        content = data.get("content") or []
        text_parts = [block.get("text", "") for block in content if isinstance(block, dict)]
        return json.loads(_strip_json("".join(text_parts)))


def _fallback_analysis(environment: EnvironmentData) -> AnalysisResult:
    species = _species_from_environment(environment)
    slope = environment.slope
    ndvi = environment.ndvi
    soil = environment.soil
    biodiversity_score = _clamp(
        28.0
        + max(0.0, 32.0 - abs(slope - 12.0))
        + max(0.0, (ndvi + 0.15) * 38.0)
        + max(0.0, (soil.organic_matter - 2.5) * 3.5),
        0.0,
        100.0,
    )
    erosion_risk = "High" if slope >= 25 else "Medium" if slope >= 12 else "Low"
    carbon_potential = round(
        max(0.5, (soil.organic_matter * 0.9) + max(0.0, ndvi + 0.05) * 6.5 + max(0.0, 18.0 - slope) * 0.06),
        2,
    )
    insight = (
        f"Estimated fallback analysis for {environment.terrain_class.lower()} terrain. "
        f"Prioritize {species[0].name} and {species[1].name} with erosion control where slope is {slope:.1f}°."
    )
    return AnalysisResult(
        biodiversity_score=round(biodiversity_score, 1),
        erosion_risk=erosion_risk,
        carbon_potential=carbon_potential,
        species=species,
        insight=insight,
        environment=environment,
    )


def _build_prompt(environment: EnvironmentData) -> str:
    return PROMPT_TEMPLATE.format(
        elevation=round(environment.elevation.elevation, 2),
        slope=round(environment.slope, 2),
        ndvi=round(environment.ndvi, 3),
        ph=round(environment.soil.ph, 2),
        nitrogen=round(environment.soil.nitrogen, 3),
        clay=round(environment.soil.clay, 2),
        organic_matter=round(environment.soil.organic_matter, 2),
    )


async def analyze_with_claude(environment: EnvironmentData) -> AnalysisResult:
    try:
        raw = await _call_claude(_build_prompt(environment))
        species = [SpeciesSuggestion(**item) for item in raw.get("species", [])]
        return AnalysisResult(
            biodiversity_score=float(raw["biodiversity_score"]),
            erosion_risk=raw["erosion_risk"],
            carbon_potential=float(raw["carbon_potential"]),
            species=species[:3],
            insight=str(raw["insight"]),
            environment=environment,
        )
    except Exception:
        return _fallback_analysis(environment)
