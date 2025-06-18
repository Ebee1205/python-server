# src/routes/admin_sandbox_api.py

from fastapi import APIRouter, Request, HTTPException
import time, uuid, orjson
from src.common.id_generator import generate_task_id
from src.utils.redis_stream_utils import redis_stream_add
from src.service.scripts.admin_sandbox_core import (
    LintRequest, TransformRequest, SweepTestRequest, LLMTestRequest
)

router = APIRouter(prefix="/v1/admin/sandbox", tags=["Sandbox"])

# 공통 핸들러
async def _publish_task(ctx, request: Request, body: dict, prompt: str):
    task_id = generate_task_id()
    tid = str(int(time.time() * 1000))

    # 이벤트명 추출
    path_parts = request.scope["path"].strip("/").split("/")
    router_tag = path_parts[2] if len(path_parts) > 2 else "sandbox"
    task_type = path_parts[3] if len(path_parts) > 3 else "unknown"
    event_type = f"{router_tag}-{task_type}"

    # 메시지 구성 및 발행
    message = {
        "event": event_type,
        "task_id": task_id,
        "prompt": prompt,
        "body": orjson.dumps(body),
        "tid": tid
    }

    stream_key = ctx.cfg.redis_consumer.stream_key
    await redis_stream_add(ctx, stream_key, message)

    # Redis 해시 TTL 설정
    await ctx.redis_handler.client.expire(f"result:{task_id}", 600)

    # 즉시 응답
    return {
        "status": "PENDING",
        "task_id": task_id
    }

@router.get("/result")
async def get_result_by_query(task_id: str, request: Request):
    ctx = request.app.state.ctx
    key = f"result:{task_id}"

    data = await ctx.redis_handler.client.hgetall(key)
    if not data:
        raise HTTPException(status_code=404, detail="Result not found")

    # Redis가 str을 반환하면 decode 없이 처리
    result = {
        k if isinstance(k, str) else k.decode(): orjson.loads(v) if (k == "output" or (isinstance(k, bytes) and k.decode() == "output")) else v if isinstance(v, str) else v.decode()
        for k, v in data.items()
    }

    # # 결과 반환 후 삭제
    # await ctx.redis_handler.client.delete(key)
    # ctx.log.info(f"[API] >> Result consumed and deleted: {key}")

    return result


# 라우팅
@router.post("/lint")
async def lint_prompt(request: Request, body: LintRequest):
    return await _publish_task(request.app.state.ctx, request, body.model_dump(), body.prompt)

@router.post("/transform")
async def transform_prompt(request: Request, body: TransformRequest):
    return await _publish_task(request.app.state.ctx, request, body.model_dump(), body.prompt)

@router.post("/sweep")
async def sweep_prompt(request: Request, body: SweepTestRequest):
    return await _publish_task(request.app.state.ctx, request, body.model_dump(), body.prompt)

@router.post("/single")
async def single_test(request: Request, body: LLMTestRequest):
    return await _publish_task(request.app.state.ctx, request, body.model_dump(), body.prompt)

@router.post("/batch")
async def batch_test(request: Request, body: LLMTestRequest):
    return await _publish_task(request.app.state.ctx, request, body.model_dump(), body.prompt)
