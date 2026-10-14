from fastapi import APIRouter, Depends, Request

from src.core.responses import build_success_response
from src.service.analyze import analyze_service
from src.service.analyze.analyze_schema import AnalyzeStateRequest
from src.service.auth.jwt_auth import require_admin


router = APIRouter(prefix="/api/analyze", tags=["Analyze"])


@router.post("/state")
async def analyze_state(
    request: Request,
    body: AnalyzeStateRequest | None = None,
    user=Depends(require_admin),
):
    """state summary + session state 기반 AI 분석 결과 조회"""
    ctx = request.app.state.ctx
    query_context = None
    if body and body.queryCtx:
        query_context = body.queryCtx.model_dump(by_alias=True, exclude_none=True)

    result = await analyze_service.analyze_state(ctx, query_context=query_context)
    return build_success_response(result)
