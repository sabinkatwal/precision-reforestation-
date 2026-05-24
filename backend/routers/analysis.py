from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.models.schemas import AnalysisRequest, AnalysisResult
from backend.routers.environment import get_environment
from backend.services.ai_service import analyze_with_claude

router = APIRouter(prefix="/analyze", tags=["analysis"])


@router.post("", response_model=AnalysisResult)
async def analyze_patch(request: AnalysisRequest) -> AnalysisResult:
    try:
        environment = await get_environment(request.lat, request.lng)
        return await analyze_with_claude(environment)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
