# src/service/scripts/admin_sandbox_service.py

from src.service.scripts.admin_sandbox_core import SandboxService, LintRequest, TransformRequest, SweepTestRequest, LLMTestRequest
import orjson, time, traceback
from pydantic import BaseModel

# 결과를 sandbox-result 이벤트로 발행
async def push_result_event(
    ctx,
    task_id: str,
    result,
    status: str = "success",
    message: str | None = None
):
    # millisecond 단위 tid
    tid = str(int(time.time() * 1000))

    payload: dict[str, any] = {
        "event": "sandbox-result",
        "tid": tid,
        "task_id": task_id,
        "status": status,
    }

    if status == "success":
        # Pydantic 모델이면 dict로 풀어서
        if isinstance(result, BaseModel):
            result = result.model_dump()
        payload["output"] = result
    else:
        payload["message"] = message or "error"

    # Redis 해시용으로 직렬화
    encoded = {}
    for k, v in payload.items():
        # 이미 문자열이면 그대로, 아니면 JSON bytes
        if isinstance(v, str):
            encoded[k] = v
        else:
            encoded[k] = orjson.dumps(v)

    try:
        # 해시 저장 & TTL 10분
        key = f"result:{task_id}"
        await ctx.redis_handler.client.hset(key, mapping=encoded)
        await ctx.redis_handler.client.expire(key, 600)

        ctx.log.info(f"[Sandbox]     >> Result: {key} ({status})")

    except Exception as e:
        # 에러 저장
        err_msg = str(e)
        tb = traceback.format_exc()
        ctx.log.error(f"[Sandbox]     !! Failed to push result for {task_id}: {err_msg}\n{tb}")

        # 실패 상태로 덮어쓰기
        error_payload = {
            "event": "sandbox-result",
            "tid": tid,
            "task_id": task_id,
            "status": "error",
            "message": err_msg,
        }
        # 문자열만 들어가도록 보장
        await ctx.redis_handler.client.hset(
            f"result:{task_id}", 
            mapping={k: str(v) for k, v in error_payload.items()}
        )
        await ctx.redis_handler.client.expire(f"result:{task_id}", 600)

        # 필요 시 호출 스택을 상위로 전달
        raise

# 단일 핸들러들
async def handle_lint_event(ctx, fields):
    task_id = fields.get("task_id")
    prompt = fields.get("prompt")
    ctx.log.info(f"[Sandbox]     -- Running LINT handler | task_id={task_id}")
    try:
        service = SandboxService(ctx)
        result = service.lint_prompt(prompt)
        await push_result_event(ctx, task_id, result)
    except Exception as e:
        await push_result_event(ctx, task_id, None, status="error", message=str(e))

async def handle_transform_event(ctx, fields):
    task_id = fields.get("task_id")
    ctx.log.info(f"[Sandbox]     -- Running TRANSFORM handler | task_id={task_id}")
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
    ctx.log.info(f"[Sandbox]     -- Running SWEEP handler | task_id={task_id}")
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
    ctx.log.info(f"[Sandbox]     -- Running SINGLE handler | task_id={task_id}")
    try:
        body = orjson.loads(fields.get("body", b"{}"))
        request = LLMTestRequest(**body)
        service = SandboxService(ctx)
        result = await service.run_single_llm_test(request)
        await push_result_event(ctx, task_id, result)
    except Exception as e:
        ctx.log.error(f"[Sandbox]     -- Single test handler error: {e}\n{traceback.format_exc()}")
        await push_result_event(ctx, task_id, None, status="error", message=str(e))

async def handle_batch_event(ctx, fields):
    task_id = fields.get("task_id")
    ctx.log.info(f"[Sandbox]     -- Running BATCH handler | task_id={task_id}")
    try:
        body = orjson.loads(fields.get("body", b"{}"))
        request = LLMTestRequest(**body)
        service = SandboxService(ctx)
        result = await service.run_batch_llm_test(request)
        await push_result_event(ctx, task_id, result)
    except Exception as e:
        await push_result_event(ctx, task_id, None, status="error", message=str(e))
