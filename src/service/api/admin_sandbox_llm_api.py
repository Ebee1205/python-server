# src/routes/admin_sandbox_api.py

from fastapi import APIRouter, Request, HTTPException
from typing import Dict, Any
import time, orjson
from src.common.id_generator import generate_task_id
from src.utils.redis_stream_utils import redis_stream_add
from src.service.scripts.admin_sandbox_core import (
    LintRequest, TransformRequest, SweepTestRequest, LLMTestRequest
)

router = APIRouter(prefix="/v1/admin/sandbox", tags=["Sandbox"])

# 공통 핸들러: 태스크 발행 및 요청 정보 저장
async def _publish_task(ctx, request: Request, body: dict, prompt: str):
    task_id = generate_task_id()
    tid = str(int(time.time() * 1000))

    # 이벤트명 추출: 마지막 path part를 task_type으로 사용
    path_parts = request.scope["path"].strip("/").split("/")
    router_tag = path_parts[2] if len(path_parts) > 2 else "sandbox"
    task_type = path_parts[-1]  # e.g. lint, transform...
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

    # Redis 해시 초기화: 요청 정보(req) 저장 및 TTL 설정
    result_key = f"result:{task_id}"
    await ctx.redis_handler.client.hset(result_key, "req", orjson.dumps(body))
    await ctx.redis_handler.client.expire(result_key, 600)

    # 즉시 응답
    return {"status": "PENDING", "task_id": task_id}

# 라우팅: 5가지 작업 유형
@router.post("/run/lint")
async def lint_prompt(request: Request, body: LintRequest):
    return await _publish_task(request.app.state.ctx, request, body.model_dump(), body.prompt)

@router.post("/run/transform")
async def transform_prompt(request: Request, body: TransformRequest):
    return await _publish_task(request.app.state.ctx, request, body.model_dump(), body.prompt)

@router.post("/run/sweep")
async def sweep_prompt(request: Request, body: SweepTestRequest):
    return await _publish_task(request.app.state.ctx, request, body.model_dump(), body.prompt)

@router.post("/run/single")
async def single_test(request: Request, body: LLMTestRequest):
    return await _publish_task(request.app.state.ctx, request, body.model_dump(), body.prompt)

@router.post("/run/batch")
async def batch_test(request: Request, body: LLMTestRequest):
    return await _publish_task(request.app.state.ctx, request, body.model_dump(), body.prompt)

# 실행 결과 조회: 요청(req) + 결과(res) 함께 반환
@router.get("/result")
async def get_result_by_query(task_id: str, request: Request):
    ctx = request.app.state.ctx
    key = f"result:{task_id}"
    data = await ctx.redis_handler.client.hgetall(key)
    if not data:
        # 결과가 더 이상 없을 때
        return {
            "status": "NO_RESULT",
            "message": f"No result available for task {task_id}"
        }

    decoded: Dict[str, Any] = {}
    for raw_k, raw_v in data.items():
        k = raw_k.decode() if isinstance(raw_k, bytes) else raw_k
        v_str = raw_v.decode() if isinstance(raw_v, bytes) else raw_v
        # JSON 필드(req, result, output)는 파싱
        if k in {"req", "result", "output"}:
            try:
                decoded[k] = orjson.loads(v_str)
            except orjson.JSONDecodeError:
                decoded[k] = v_str
        else:
            decoded[k] = v_str

    # 결과가 저장되지 않았을 때 (req만 있는 경우)
    if not decoded.get("result") and not decoded.get("output"):
        return {
            "status": "NO_RESULT",
            "task_id": decoded.get("task_id"),
            "req": decoded.get("req"),
            "message": f"Result pending for task {task_id}"
        }

    # 응답 구조: 요청(req)와 서비스 결과(res)를 함께 반환
    return {
        "status": decoded.get("status"),
        "tid": decoded.get("tid"),
        "event": decoded.get("event"),
        "task_id": decoded.get("task_id"),
        "req": decoded.get("req"),
        "res": decoded.get("result") or decoded.get("output")
    }