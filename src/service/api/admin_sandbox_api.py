from fastapi import APIRouter, Request
import time, uuid, orjson

from service.scripts.admin_sandbox_service import (
    TransformRequest, LintRequest, SweepTestRequest, LLMTestRequest
)
from src.utils.redis_stream_utils import redis_stream_add
from src.utils.redis_hash_utils import (
    redis_hset_multi, redis_hget, redis_hexists
)
from src.common.common_codes import ResponseStatus

router = APIRouter(prefix="/v1/admin/sandbox", tags=["Sandbox"])

def _create_response(status: dict, tid: int, prompt: str, result: any):
    return {
        "status": status,
        "tid": tid,
        "prompt": prompt,
        "result": result
    }

async def _publish_task(ctx, request: Request, body: dict, prompt: str):
    task_id = str(uuid.uuid4())
    tid = int(time.time() * 1000)

    path_parts = request.scope["path"].strip("/").split("/")
    router_tag = path_parts[2] if len(path_parts) > 2 else "sandbox"
    task_type = path_parts[3] if len(path_parts) > 3 else "unknown"
    event_type = f"{router_tag}-{task_type}"

    message = {
        "task_id": task_id,
        "event": event_type,
        "prompt": prompt,
        "body": orjson.dumps(body)
    }

    result_key = f"result:{task_id}"

    # hash 저장
    await redis_hset_multi(ctx, result_key, {
        "event": event_type,
        "prompt": prompt,
        "body": orjson.dumps(body),
        "status": "pending",
        "tid": str(tid)
    })
    # TTL 설정 (예: 10분 후 만료)
    await ctx.redis_handler.client.expire(result_key, 600)

    ctx.log.info(f"[API]     >> Task Registered: event={event_type}, task_id={task_id}")


    return _create_response(
        status=ResponseStatus.SUCCESS,
        tid=tid,
        prompt=prompt,
        result={
            "task_id": task_id,
            "message": f"Task '{event_type}' accepted. Use /result/{{task_id}} to retrieve result."
        }
    )

@router.get("/result/{task_id}")
async def get_result(request: Request, task_id: str):
    ctx = request.app.state.ctx
    key = f"result:{task_id}"

    exists = await redis_hexists(ctx, key, "output")
    if not exists:
        return {
            "status": ResponseStatus.NOT_FOUND,
            "result": f"No result for task_id={task_id}"
        }

    prompt = await redis_hget(ctx, key, "prompt")
    output = await redis_hget(ctx, key, "output")

    return {
        "status": ResponseStatus.SUCCESS,
        "tid": int(time.time() * 1000),
        "prompt": prompt,
        "result": orjson.loads(output or "{}")
    }

@router.post("/lint")
async def lint_prompt(request: Request, body: LintRequest):
    ctx = request.app.state.ctx
    return await _publish_task(ctx, request, body.model_dump(), body.prompt)

@router.post("/transform")
async def transform_prompt(request: Request, body: TransformRequest):
    ctx = request.app.state.ctx
    return await _publish_task(ctx, request, body.model_dump(), body.prompt)

@router.post("/sweep")
async def sweep_parameters(request: Request, body: SweepTestRequest):
    ctx = request.app.state.ctx
    return await _publish_task(ctx, request, body.model_dump(), body.prompt)

@router.post("/single")
async def single_llm_test(request: Request, body: LLMTestRequest):
    ctx = request.app.state.ctx
    return await _publish_task(ctx, request, body.model_dump(), body.prompt)

@router.post("/batch")
async def batch_llm_test(request: Request, body: LLMTestRequest):
    ctx = request.app.state.ctx
    return await _publish_task(ctx, request, body.model_dump(), body.prompt)

# 결과 저장 예시 (consumer 측)
# from src.utils.redis_hash_utils import redis_hset_multi

# # 저장 예시
# await redis_hset_multi(ctx, f"result:{task_id}", {
#     "status": "success",
#     "prompt": prompt,
#     "output": orjson.dumps(result),
#     "tid": str(tid)
# })
# await ctx.redis_handler.client.expire(f"result:{task_id}", 600)
