# api 기본 예제
# service/api/basic_api.py

from fastapi import APIRouter, Request

import src.common.common_codes as codes
from src.service.scripts import basic_service
from src.utils import rabbitmq_utils

# 라우터 등록은 여기서 하고 실제 로직은 service에서 관리
# http://localhost:8000/
# GET /v1/basic/ping
router = APIRouter(prefix="/v1/basic", tags=["Basic"])

@router.get("/ping")
async def ping(request: Request):
    ctx = request.app.state.ctx
    return basic_service.ping(ctx)

@router.post("/rmq")
async def publish_to_rmq(request: Request):
    data = await request.json()
    ctx = request.app.state.ctx

    queue = "ankoko-from-algo"
    await rabbitmq_utils.rmq_send_response(ctx, queue, data)
    return {
                "queue": queue,
                "codes": {
                    **codes.ResponseStatus.SUCCESS,
                }
            }

from src.service.scripts.basic_service import handle_test_ping
@router.post("/test-ping")
async def redis_test_ping(request: Request):
    ctx = request.app.state.ctx
    data = await request.json()
    user_id = data.get("userId", "test-user")
    return await handle_test_ping(ctx, user_id)
