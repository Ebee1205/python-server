from fastapi import APIRouter, Request, Body
from pydantic import BaseModel

router = APIRouter(prefix="/v1/admin", tags=["Admin"])

# ---- 요청 바디 스키마 정의 ----
class PatternTranslateRequest(BaseModel):
    code: str  # JS function(x, y, p, ctx)

@router.post("/patterns/parse")
async def translate_pattern(request: Request, body: PatternTranslateRequest):
    """
    사용자 JS draw 함수를 받아 patterns[] 항목 포맷으로 변환
    """
    ctx = request.app.state.ctx
    llm = ctx.llm_manager["ops"]
    result = await llm.convert_pattern(body.code)

    return {
        "success": True,
        "result": result
    }