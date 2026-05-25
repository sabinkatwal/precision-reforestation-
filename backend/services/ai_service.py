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

{{
  "biodiversity_score": number (0-100),
  "erosion_risk": "Low | Medium | High",
  "carbon_potential": number (tons/year),
  "species": [
    {{
      "name": string,
      "confidence": number (0-100),
      "reason": string
    }}
  ],
  "insight": string
}}
"""


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def _score(value: float, ideal: float, tolerance: float) -> float:
    """
    Gaussian-shaped score: 1.0 when value == ideal, decays as value moves away.
    tolerance = 1-sigma width; score is ~0.6 at 1 sigma, ~0.14 at 2 sigma.
    """
    return float(_clamp(((value - ideal) ** 2) / -(2 * tolerance ** 2), -10, 0))


def _gaussian(value: float, ideal: float, tolerance: float) -> float:
    import math
    return math.exp(_score(value, ideal, tolerance))


def _dynamic_confidence(
    base: float,
    elevation: float,
    slope: float,
    ndvi: float,
    ph: float,
    nitrogen: float,
    organic_matter: float,
    # Species-specific ecological optima
    elev_ideal: float,
    elev_tol: float,
    ph_ideal: float,
    ph_tol: float,
    ndvi_ideal: float,
    ndvi_tol: float,
    slope_max: float,          # species fails on slopes steeper than this
    nitrogen_ideal: float,
    nitrogen_tol: float,
    om_ideal: float,
    om_tol: float,
) -> int:
    """
    Compute dynamic confidence by multiplying Gaussian fit scores for each
    environmental parameter against the species' ecological optimum.

    Final confidence = base × (weighted product of fit scores), clamped 30–97.
    """
    # --- Individual fit scores (0.0 – 1.0) ---
    elev_fit     = _gaussian(elevation,     elev_ideal,     elev_tol)
    ph_fit       = _gaussian(ph,            ph_ideal,       ph_tol)
    ndvi_fit     = _gaussian(ndvi,          ndvi_ideal,     ndvi_tol)
    nitrogen_fit = _gaussian(nitrogen,      nitrogen_ideal, nitrogen_tol)
    om_fit       = _gaussian(organic_matter, om_ideal,      om_tol)

    # Slope penalty: linear drop-off beyond species slope tolerance
    slope_fit = _clamp(1.0 - max(0.0, slope - slope_max) / 30.0, 0.0, 1.0)

    # --- Weighted composite (weights sum to 1.0) ---
    composite = (
        0.30 * elev_fit      +   # elevation is most critical
        0.20 * ph_fit        +   # soil pH strongly constrains species
        0.18 * ndvi_fit      +   # vegetation cover proxy
        0.14 * slope_fit     +   # terrain suitability
        0.10 * nitrogen_fit  +   # nutrient availability
        0.08 * om_fit            # organic enrichment
    )

    # Scale: base confidence × composite, then clamp to realistic range
    raw = base * composite
    return int(_clamp(round(raw), 30, 97))


def _species_from_environment(environment: EnvironmentData) -> List[SpeciesSuggestion]:
    elevation     = environment.elevation.elevation
    slope         = environment.slope
    ndvi          = environment.ndvi
    soil          = environment.soil
    ph            = soil.ph
    nitrogen      = soil.nitrogen
    organic_matter = soil.organic_matter

    # Shared kwargs passed to every _dynamic_confidence call
    env = dict(
        elevation=elevation, slope=slope, ndvi=ndvi,
        ph=ph, nitrogen=nitrogen, organic_matter=organic_matter,
    )

    species: List[SpeciesSuggestion] = []

    # ── Terai / tropical lowland (<900 m) ────────────────────────────────────
    if elevation < 900:
        species.append(SpeciesSuggestion(
            name="Shorea robusta (Sal)",
            confidence=_dynamic_confidence(
                95, **env,
                elev_ideal=500,  elev_tol=400,
                ph_ideal=6.5,    ph_tol=0.8,
                ndvi_ideal=0.45, ndvi_tol=0.25,
                slope_max=15,
                nitrogen_ideal=5.0, nitrogen_tol=2.5,
                om_ideal=4.0,    om_tol=2.0,
            ),
            reason="Dominant low-elevation Terai species; thrives in warm, fertile alluvial soils.",
        ))
        species.append(SpeciesSuggestion(
            name="Dalbergia sissoo (Sisau)",
            confidence=_dynamic_confidence(
                92, **env,
                elev_ideal=350,  elev_tol=350,
                ph_ideal=7.0,    ph_tol=1.0,
                ndvi_ideal=0.30, ndvi_tol=0.30,
                slope_max=20,
                nitrogen_ideal=4.0, nitrogen_tol=3.0,
                om_ideal=3.0,    om_tol=2.0,
            ),
            reason="Fast-growing nitrogen-fixer ideal for riverine and degraded lowland restoration.",
        ))
        species.append(SpeciesSuggestion(
            name="Tectona grandis (Sagwan / Teak)",
            confidence=_dynamic_confidence(
                90, **env,
                elev_ideal=400,  elev_tol=400,
                ph_ideal=6.5,    ph_tol=1.0,
                ndvi_ideal=0.40, ndvi_tol=0.25,
                slope_max=15,
                nitrogen_ideal=5.0, nitrogen_tol=2.0,
                om_ideal=4.5,    om_tol=2.0,
            ),
            reason="High-value timber tree suited to moist tropical lowlands with deep loamy soils.",
        ))
        species.append(SpeciesSuggestion(
            name="Bombax ceiba (Simal)",
            confidence=_dynamic_confidence(
                88, **env,
                elev_ideal=300,  elev_tol=300,
                ph_ideal=6.8,    ph_tol=1.2,
                ndvi_ideal=0.20, ndvi_tol=0.30,
                slope_max=25,
                nitrogen_ideal=3.5, nitrogen_tol=2.5,
                om_ideal=3.0,    om_tol=2.5,
            ),
            reason="Pioneer deciduous tree that colonises disturbed Terai land quickly.",
        ))
        species.append(SpeciesSuggestion(
            name="Terminalia alata (Saj)",
            confidence=_dynamic_confidence(
                86, **env,
                elev_ideal=600,  elev_tol=400,
                ph_ideal=6.5,    ph_tol=1.0,
                ndvi_ideal=0.35, ndvi_tol=0.25,
                slope_max=20,
                nitrogen_ideal=4.0, nitrogen_tol=2.5,
                om_ideal=3.5,    om_tol=2.0,
            ),
            reason="Mixed Shorea-Saj forest associate; tolerates seasonally dry Terai conditions.",
        ))
        species.append(SpeciesSuggestion(
            name="Acacia catechu (Khair)",
            confidence=_dynamic_confidence(
                85, **env,
                elev_ideal=400,  elev_tol=400,
                ph_ideal=7.0,    ph_tol=1.2,
                ndvi_ideal=0.20, ndvi_tol=0.30,
                slope_max=25,
                nitrogen_ideal=3.0, nitrogen_tol=3.0,
                om_ideal=2.5,    om_tol=2.0,
            ),
            reason="Drought-hardy agroforestry species common in Terai buffer-zone plantations.",
        ))

    # ── Subtropical mid-hills (900–1 800 m) ──────────────────────────────────
    elif elevation < 1800:
        species.append(SpeciesSuggestion(
            name="Pinus roxburghii (Khote Sallo / Chir Pine)",
            confidence=_dynamic_confidence(
                95, **env,
                elev_ideal=1300, elev_tol=400,
                ph_ideal=5.8,    ph_tol=0.8,
                ndvi_ideal=0.35, ndvi_tol=0.25,
                slope_max=35,
                nitrogen_ideal=3.5, nitrogen_tol=2.5,
                om_ideal=2.5,    om_tol=1.5,
            ),
            reason="Dominant mid-elevation pine; resilient on disturbed, dry south-facing slopes.",
        ))
        species.append(SpeciesSuggestion(
            name="Alnus nepalensis (Utis / Himalayan Alder)",
            confidence=_dynamic_confidence(
                93, **env,
                elev_ideal=1200, elev_tol=500,
                ph_ideal=6.0,    ph_tol=1.0,
                ndvi_ideal=0.25, ndvi_tol=0.30,
                slope_max=40,
                nitrogen_ideal=5.0, nitrogen_tol=3.0,
                om_ideal=3.5,    om_tol=2.0,
            ),
            reason="Nitrogen-fixing pioneer; rapidly stabilises landslide scars and eroded hillsides.",
        ))
        species.append(SpeciesSuggestion(
            name="Castanopsis indica (Katus)",
            confidence=_dynamic_confidence(
                91, **env,
                elev_ideal=1500, elev_tol=400,
                ph_ideal=5.5,    ph_tol=0.8,
                ndvi_ideal=0.50, ndvi_tol=0.20,
                slope_max=30,
                nitrogen_ideal=5.0, nitrogen_tol=2.5,
                om_ideal=5.0,    om_tol=2.0,
            ),
            reason="Broadleaf evergreen dominant in moist subtropical forests; high biodiversity value.",
        ))
        species.append(SpeciesSuggestion(
            name="Schima wallichii (Chilaune)",
            confidence=_dynamic_confidence(
                89, **env,
                elev_ideal=1400, elev_tol=400,
                ph_ideal=5.5,    ph_tol=1.0,
                ndvi_ideal=0.40, ndvi_tol=0.25,
                slope_max=35,
                nitrogen_ideal=4.0, nitrogen_tol=2.5,
                om_ideal=4.0,    om_tol=2.0,
            ),
            reason="Fire-tolerant broadleaf associate of Chir Pine; enriches mixed forest structure.",
        ))
        species.append(SpeciesSuggestion(
            name="Michelia champaca (Champ)",
            confidence=_dynamic_confidence(
                87, **env,
                elev_ideal=1000, elev_tol=300,
                ph_ideal=6.0,    ph_tol=0.8,
                ndvi_ideal=0.45, ndvi_tol=0.20,
                slope_max=25,
                nitrogen_ideal=5.0, nitrogen_tol=2.0,
                om_ideal=5.0,    om_tol=2.0,
            ),
            reason="Valuable timber and fragrant flowering tree of warm subtropical valleys.",
        ))
        species.append(SpeciesSuggestion(
            name="Myrica esculenta (Kafal)",
            confidence=_dynamic_confidence(
                85, **env,
                elev_ideal=1600, elev_tol=400,
                ph_ideal=5.8,    ph_tol=0.8,
                ndvi_ideal=0.40, ndvi_tol=0.25,
                slope_max=30,
                nitrogen_ideal=4.0, nitrogen_tol=2.5,
                om_ideal=4.0,    om_tol=2.0,
            ),
            reason="Native mid-hill fruit tree that supports birds and small mammals.",
        ))

    # ── Temperate / montane (1 800–2 800 m) ──────────────────────────────────
    elif elevation < 2800:
        species.append(SpeciesSuggestion(
            name="Quercus lanata (Banjh Oak)",
            confidence=_dynamic_confidence(
                95, **env,
                elev_ideal=2300, elev_tol=500,
                ph_ideal=5.5,    ph_tol=0.8,
                ndvi_ideal=0.55, ndvi_tol=0.20,
                slope_max=35,
                nitrogen_ideal=5.0, nitrogen_tol=2.5,
                om_ideal=6.0,    om_tol=2.0,
            ),
            reason="Dominant temperate oak; robust carbon store and fodder resource in montane Nepal.",
        ))
        species.append(SpeciesSuggestion(
            name="Rhododendron arboreum (Lali Gurans)",
            confidence=_dynamic_confidence(
                92, **env,
                elev_ideal=2400, elev_tol=500,
                ph_ideal=4.8,    ph_tol=0.6,
                ndvi_ideal=0.50, ndvi_tol=0.20,
                slope_max=40,
                nitrogen_ideal=3.5, nitrogen_tol=2.0,
                om_ideal=7.0,    om_tol=2.5,
            ),
            reason="National flower; thrives in acidic montane soils and supports pollinator diversity.",
        ))
        species.append(SpeciesSuggestion(
            name="Betula alnoides (Saur Salla Birch)",
            confidence=_dynamic_confidence(
                90, **env,
                elev_ideal=2500, elev_tol=400,
                ph_ideal=5.5,    ph_tol=0.8,
                ndvi_ideal=0.30, ndvi_tol=0.30,
                slope_max=40,
                nitrogen_ideal=4.0, nitrogen_tol=2.5,
                om_ideal=5.0,    om_tol=2.0,
            ),
            reason="Pioneer birch that regenerates degraded upper-temperate slopes quickly.",
        ))
        species.append(SpeciesSuggestion(
            name="Acer campbellii (Maple)",
            confidence=_dynamic_confidence(
                88, **env,
                elev_ideal=2200, elev_tol=400,
                ph_ideal=5.8,    ph_tol=0.8,
                ndvi_ideal=0.45, ndvi_tol=0.20,
                slope_max=30,
                nitrogen_ideal=4.5, nitrogen_tol=2.0,
                om_ideal=5.5,    om_tol=2.0,
            ),
            reason="Broadleaf maple adding structural diversity and autumn forage to temperate forests.",
        ))
        species.append(SpeciesSuggestion(
            name="Lyonia ovalifolia (Angeri)",
            confidence=_dynamic_confidence(
                86, **env,
                elev_ideal=2000, elev_tol=400,
                ph_ideal=5.0,    ph_tol=0.7,
                ndvi_ideal=0.40, ndvi_tol=0.25,
                slope_max=35,
                nitrogen_ideal=3.0, nitrogen_tol=2.0,
                om_ideal=6.0,    om_tol=2.5,
            ),
            reason="Ericaceous understorey shrub-tree that restores acidic montane forest understoreys.",
        ))
        species.append(SpeciesSuggestion(
            name="Prunus cerasoides (Paiyun / Wild Cherry)",
            confidence=_dynamic_confidence(
                84, **env,
                elev_ideal=2000, elev_tol=500,
                ph_ideal=6.0,    ph_tol=0.8,
                ndvi_ideal=0.40, ndvi_tol=0.25,
                slope_max=30,
                nitrogen_ideal=4.0, nitrogen_tol=2.5,
                om_ideal=4.5,    om_tol=2.0,
            ),
            reason="Wildlife-friendly fruiting tree suited to mid-montane valley edges.",
        ))

    # ── Subalpine / alpine (≥2 800 m) ────────────────────────────────────────
    else:
        species.append(SpeciesSuggestion(
            name="Abies spectabilis (Talispatra / Himalayan Fir)",
            confidence=_dynamic_confidence(
                95, **env,
                elev_ideal=3500, elev_tol=600,
                ph_ideal=5.5,    ph_tol=0.8,
                ndvi_ideal=0.50, ndvi_tol=0.20,
                slope_max=35,
                nitrogen_ideal=3.5, nitrogen_tol=2.0,
                om_ideal=8.0,    om_tol=3.0,
            ),
            reason="Dominant subalpine conifer forming dense stands near the treeline.",
        ))
        species.append(SpeciesSuggestion(
            name="Betula utilis (Bhojpatra / Himalayan Birch)",
            confidence=_dynamic_confidence(
                93, **env,
                elev_ideal=3800, elev_tol=600,
                ph_ideal=5.0,    ph_tol=0.7,
                ndvi_ideal=0.30, ndvi_tol=0.25,
                slope_max=40,
                nitrogen_ideal=3.0, nitrogen_tol=2.0,
                om_ideal=7.0,    om_tol=3.0,
            ),
            reason="Key treeline species; pioneer on glacial moraines and avalanche tracks.",
        ))
        species.append(SpeciesSuggestion(
            name="Rhododendron campanulatum (Bell Gurans)",
            confidence=_dynamic_confidence(
                91, **env,
                elev_ideal=4000, elev_tol=600,
                ph_ideal=4.5,    ph_tol=0.6,
                ndvi_ideal=0.25, ndvi_tol=0.20,
                slope_max=45,
                nitrogen_ideal=2.5, nitrogen_tol=1.5,
                om_ideal=9.0,    om_tol=3.0,
            ),
            reason="Subalpine rhododendron that stabilises steep rocky terrain above 3 000 m.",
        ))
        species.append(SpeciesSuggestion(
            name="Pinus wallichiana (Gobre Sallo / Blue Pine)",
            confidence=_dynamic_confidence(
                89, **env,
                elev_ideal=3200, elev_tol=600,
                ph_ideal=5.8,    ph_tol=0.8,
                ndvi_ideal=0.35, ndvi_tol=0.25,
                slope_max=35,
                nitrogen_ideal=3.0, nitrogen_tol=2.0,
                om_ideal=5.0,    om_tol=2.5,
            ),
            reason="Tall subalpine pine well adapted to rocky, well-drained high-altitude soils.",
        ))
        species.append(SpeciesSuggestion(
            name="Juniperus recurva (Dhup Salla / Drooping Juniper)",
            confidence=_dynamic_confidence(
                87, **env,
                elev_ideal=4200, elev_tol=700,
                ph_ideal=6.5,    ph_tol=1.0,
                ndvi_ideal=0.15, ndvi_tol=0.20,
                slope_max=50,
                nitrogen_ideal=2.0, nitrogen_tol=1.5,
                om_ideal=4.0,    om_tol=3.0,
            ),
            reason="Drought- and cold-tolerant juniper; crucial ground cover above 3 500 m.",
        ))
        species.append(SpeciesSuggestion(
            name="Sorbus microphylla (Himalayan Whitebeam)",
            confidence=_dynamic_confidence(
                85, **env,
                elev_ideal=3500, elev_tol=500,
                ph_ideal=5.5,    ph_tol=0.8,
                ndvi_ideal=0.25, ndvi_tol=0.25,
                slope_max=40,
                nitrogen_ideal=2.5, nitrogen_tol=2.0,
                om_ideal=6.0,    om_tol=2.5,
            ),
            reason="Small subalpine tree providing berries for wildlife near the treeline.",
        ))

    # ── Cross-cutting modifiers ───────────────────────────────────────────────
    extra: List[SpeciesSuggestion] = []

    if ndvi > 0.45 and organic_matter > 4:
        extra.append(SpeciesSuggestion(
            name="Schima wallichii (Chilaune)",
            confidence=_dynamic_confidence(
                88, **env,
                elev_ideal=1400, elev_tol=600,
                ph_ideal=5.5,    ph_tol=1.0,
                ndvi_ideal=0.55, ndvi_tol=0.15,
                slope_max=35,
                nitrogen_ideal=4.5, nitrogen_tol=2.5,
                om_ideal=5.0,    om_tol=2.0,
            ),
            reason="Thrives where canopy recovery and mixed broadleaf structure are already emerging.",
        ))
    if slope > 20:
        extra.append(SpeciesSuggestion(
            name="Bambusa nutans (Mal Bans)",
            confidence=_dynamic_confidence(
                88, **env,
                elev_ideal=800,  elev_tol=700,
                ph_ideal=6.0,    ph_tol=1.2,
                ndvi_ideal=0.30, ndvi_tol=0.30,
                slope_max=50,
                nitrogen_ideal=4.0, nitrogen_tol=3.0,
                om_ideal=3.5,    om_tol=2.5,
            ),
            reason="Rapid slope-binding bamboo; excellent soil reinforcement on steeper terrain.",
        ))
    if ph < 5.5:
        extra.append(SpeciesSuggestion(
            name="Rhododendron arboreum (Lali Gurans)",
            confidence=_dynamic_confidence(
                88, **env,
                elev_ideal=2400, elev_tol=800,
                ph_ideal=4.8,    ph_tol=0.5,
                ndvi_ideal=0.45, ndvi_tol=0.20,
                slope_max=40,
                nitrogen_ideal=3.5, nitrogen_tol=2.0,
                om_ideal=7.0,    om_tol=2.5,
            ),
            reason="Acid-tolerant native broadleaf; supports biodiversity on low-pH soils.",
        ))
    if nitrogen > 6:
        extra.append(SpeciesSuggestion(
            name="Alnus nepalensis (Utis)",
            confidence=_dynamic_confidence(
                88, **env,
                elev_ideal=1200, elev_tol=600,
                ph_ideal=6.0,    ph_tol=1.0,
                ndvi_ideal=0.25, ndvi_tol=0.30,
                slope_max=40,
                nitrogen_ideal=7.0, nitrogen_tol=2.0,
                om_ideal=4.0,    om_tol=2.0,
            ),
            reason="Nitrogen-fixer that thrives and further enriches high-nitrogen riparian soils.",
        ))
    if not extra:
        extra.append(SpeciesSuggestion(
            name="Celtis australis (Khari / Nettle Tree)",
            confidence=_dynamic_confidence(
                86, **env,
                elev_ideal=1000, elev_tol=800,
                ph_ideal=6.5,    ph_tol=1.2,
                ndvi_ideal=0.35, ndvi_tol=0.30,
                slope_max=30,
                nitrogen_ideal=4.0, nitrogen_tol=3.0,
                om_ideal=4.0,    om_tol=2.5,
            ),
            reason="Versatile native tree for multi-strata restoration on moderately stable ground.",
        ))

    # Deduplicate by name, primary zone list takes priority
    seen = {s.name for s in species}
    for e in extra:
        if e.name not in seen:
            species.append(e)
            seen.add(e.name)

    # Return top 5 sorted by dynamic confidence
    species.sort(key=lambda s: s.confidence, reverse=True)
    return species[:5]


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
        "messages": [{"role": "user", "content": prompt}],
    }
    timeout = httpx.Timeout(settings.api_timeout_seconds)
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(
            "https://api.anthropic.com/v1/messages", headers=headers, json=payload
        )
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
            species=species[:5],
            insight=str(raw["insight"]),
            environment=environment,
        )
    except Exception:
        return _fallback_analysis(environment)