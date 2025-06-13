from fastapi import APIRouter, Request
import time, uuid, orjson
from service.scripts.admin_sandbox_service import (
    TransformRequest, LintRequest, SweepTestRequest, LLMTestRequest
)
from src.utils.redis_stream_utils import redis_stream_add, redis_stream_find_result
from src.common.common_codes import ResponseStatus

router = APIRouter(prefix="/v1/admin/sandbox", tags=["Sandbox"])

def _create_response(status: dict, tid: int, prompt: str, result: any):
    return {
        "status": status,
        "tid": tid,
        "prompt": prompt,
        "result": result
    }

async def _publish_task(ctx, type_: str, body: dict, prompt: str):
    task_id = str(uuid.uuid4())
    tid = int(time.time() * 1000)

    message = {
        "task_id": task_id,
        "type": type_,
        "prompt": prompt,
        "body": orjson.dumps(body)
    }

    await redis_stream_add(ctx, "ai_task_stream", message)

    ctx.log.info(f"[API]     >> Task Published: type={type_}, task_id={task_id}")

    return {
        "status": ResponseStatus.SUCCESS,
        "tid": tid,
        "prompt": prompt,
        "result": {
            "task_id": task_id,
            "message": f"Task '{type_}' accepted. Use /result/{task_id} to retrieve result."
        }
    }

@router.get("/result/{task_id}")
async def get_task_result(request: Request, task_id: str):
    ctx = request.app.state.ctx
    stream_key = "sandbox_result_stream"  # 하나의 스트림만 사용

    result = await redis_stream_find_result(ctx, stream_key, task_id)

    if result:
        return result
    else:
        return {
            "status": ResponseStatus.NOT_FOUND,
            "result": f"No result for task_id={task_id}"
        }



@router.post("/lint")
async def lint_prompt(request: Request, body: LintRequest):
    ctx = request.app.state.ctx
    return await _publish_task(ctx, "lint", body.model_dump(), body.prompt)

@router.post("/transform")
async def transform_prompt(request: Request, body: TransformRequest):
    ctx = request.app.state.ctx
    return await _publish_task(ctx, "transform", body.model_dump(), body.prompt)

@router.post("/sweep")
async def sweep_parameters(request: Request, body: SweepTestRequest):
    ctx = request.app.state.ctx
    return await _publish_task(ctx, "sweep", body.model_dump(), body.prompt)

@router.post("/single")
async def single_llm_test(request: Request, body: LLMTestRequest):
    ctx = request.app.state.ctx
    return await _publish_task(ctx, "single", body.model_dump(), body.prompt)

@router.post("/batch")
async def batch_llm_test(request: Request, body: LLMTestRequest):
    ctx = request.app.state.ctx
    return await _publish_task(ctx, "batch", body.model_dump(), body.prompt)
