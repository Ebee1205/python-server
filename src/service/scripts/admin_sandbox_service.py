# src/service/scripts/admin_sandbox_service.py

from src.service.scripts.admin_sandbox_core import SandboxService, LintRequest, TransformRequest, SweepTestRequest, LLMTestRequest
import orjson, time, traceback
from pydantic import BaseModel

# 결과를 sandbox-result 이벤트로 발행
async def push_result_event(ctx, task_id, result, status="success", message=None):
    tid = str(int(time.time() * 1000))
    try:
        payload = {
            "event": "sandbox-result",
            "tid": tid,
            "task_id": task_id,
            "status": status,
        }
        if status == "success":
            if isinstance(result, BaseModel):
                result = result.model_dump()
            payload["output"] = result
        else:
            payload["message"] = message or "error"

        # 직렬화 및 해시 저장
        encoded = {
            k: v if isinstance(v, str) else orjson.dumps(v)
            for k, v in payload.items()
        }
        await ctx.redis_handler.client.hset(f"result:{task_id}", mapping=encoded)
        await ctx.redis_handler.client.expire(f"result:{task_id}", 600)
        ctx.log.info(f"[REDIS] >> Result stored in result:{task_id}")
    except Exception as e:
        ctx.log.error(f"[REDIS] !! Failed to store result: {e}")

# 단일 핸들러들
async def handle_lint_event(ctx, fields):
    task_id = fields.get("task_id")
    prompt = fields.get("prompt")
    ctx.log.info(f"[SANDBOX] -- Running LINT handler | task_id={task_id}")
    try:
        service = SandboxService(ctx)
        result = service.lint_prompt(prompt)
        await push_result_event(ctx, task_id, result)
    except Exception as e:
        await push_result_event(ctx, task_id, None, status="error", message=str(e))

async def handle_transform_event(ctx, fields):
    task_id = fields.get("task_id")
    ctx.log.info(f"[SANDBOX] -- Running TRANSFORM handler | task_id={task_id}")
    try:
        body = orjson.loads(fields.get("body", b"{}"))
        request = TransformRequest(**body)
        service = SandboxService(ctx)
        transformed = service.transform_prompt(request.prompt, transform_type="wrap_in_instruction", analysis_type=request.analysis_type)
        await push_result_event(ctx, task_id, {"original": request.prompt, "transformed": transformed})
    except Exception as e:
        await push_result_event(ctx, task_id, None, status="error", message=str(e))

async def handle_sweep_event(ctx, fields):
    task_id = fields.get("task_id")
    ctx.log.info(f"[SANDBOX] -- Running SWEEP handler | task_id={task_id}")
    try:
        body = orjson.loads(fields.get("body", b"{}"))
        request = SweepTestRequest(**body)
        service = SandboxService(ctx)
        result = await service.run_sweep_test(request.prompt, request.sweep)
        await push_result_event(ctx, task_id, result)
    except Exception as e:
        await push_result_event(ctx, task_id, None, status="error", message=str(e))

async def handle_single_event(ctx, fields):
    task_id = fields.get("task_id")
    ctx.log.info(f"[SANDBOX] -- Running SINGLE handler | task_id={task_id}")
    try:
        body = orjson.loads(fields.get("body", b"{}"))
        request = LLMTestRequest(**body)
        service = SandboxService(ctx)
        result = await service.run_single_llm_test(request)
        await push_result_event(ctx, task_id, result)
    except Exception as e:
        ctx.log.error(f"[REDIS] -- Single test handler error: {e}\n{traceback.format_exc()}")
        await push_result_event(ctx, task_id, None, status="error", message=str(e))

async def handle_batch_event(ctx, fields):
    task_id = fields.get("task_id")
    ctx.log.info(f"[SANDBOX] -- Running BATCH handler | task_id={task_id}")
    try:
        body = orjson.loads(fields.get("body", b"{}"))
        request = LLMTestRequest(**body)
        service = SandboxService(ctx)
        result = await service.run_batch_llm_test(request)
        await push_result_event(ctx, task_id, result)
    except Exception as e:
        await push_result_event(ctx, task_id, None, status="error", message=str(e))
