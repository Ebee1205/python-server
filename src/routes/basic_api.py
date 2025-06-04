# routes/basic_api.py

from fastapi import APIRouter, Request
from src.service.scripts import basic_service

# 라우터 등록은 여기서 하고 실제 로직은 service에서 관리
# http://localhost:8000/docs
# GET /v1/basic/ping
router = APIRouter(prefix="/v1/basic", tags=["Basic"])

@router.get("/ping")
async def ping(request: Request):
    ctx = request.app.state.ctx
    return basic_service.ping(ctx)