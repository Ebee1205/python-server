from fastapi import APIRouter, Request
import time

from service.scripts.admin_sandbox_service import (
    SandboxService, TransformRequest, LintRequest, 
    SweepTestRequest, LLMTestRequest
)
from src.common.common_codes import ResponseStatus
from src.utils import rabbitmq_utils

router = APIRouter(prefix="/v1/admin/sandbox", tags=["Sandbox"])

def _create_response(status_code: str, message: str, tid: int, prompt: str, result: any):
    """공통 응답 형식 생성"""
    return {
        "status": {"code": status_code, "msg": message},
        "tid": tid,
        "prompt": prompt,
        "result": result
    }

@router.post("/lint")
async def lint_prompt(request: Request, body: LintRequest):
    """프롬프트 린트 검사"""
    ctx = request.app.state.ctx
    service = SandboxService(ctx)
    
    try:
        result = service.lint_prompt(body.prompt)
        status = ResponseStatus.SUCCESS if not result["issues"] else {
            "code": "E0400", "msg": "프롬프트 검사 결과 문제 있음"
        }
        return _create_response(status, int(time.time() * 1000), body.prompt, result)
    
    except Exception as e:
        ctx.log.error(f"[Sandbox] Lint error: {str(e)}")
        return _create_response(ResponseStatus.SERVER_ERROR, int(time.time() * 1000), body.prompt, {})


@router.post("/transform")
async def transform_prompt(request: Request, body: TransformRequest):
    """프롬프트 변환"""
    ctx = request.app.state.ctx
    service = SandboxService(ctx)
    
    try:
        result = service.transform_prompt(body.prompt, body.type, body.analysis_type)
        return _create_response(ResponseStatus.SUCCESS, int(time.time() * 1000), body.prompt, result)
    
    except Exception as e:
        ctx.log.error(f"[Sandbox] Transform error: {str(e)}")
        return _create_response(ResponseStatus.SERVER_ERROR, int(time.time() * 1000), body.prompt, "")


@router.post("/sweep")
async def sweep_parameters(request: Request, body: SweepTestRequest):
    """파라미터 스위프 테스트"""
    ctx = request.app.state.ctx
    service = SandboxService(ctx)
    
    try:
        results = await service.run_sweep_test(body.prompt, body.sweep)
        return _create_response(ResponseStatus.SUCCESS, int(time.time() * 1000), body.prompt, results)
    
    except ValueError as e:
        return _create_response(ResponseStatus.BAD_REQUEST, int(time.time() * 1000), body.prompt, [])
    
    except Exception as e:
        ctx.log.error(f"[Sandbox] Sweep error: {str(e)}")
        return _create_response(ResponseStatus.SERVER_ERROR, int(time.time() * 1000), body.prompt, [])

@router.post("/single")
async def single_llm_test(request: Request, body: LLMTestRequest):
    """단일 LLM 테스트"""
    ctx = request.app.state.ctx
    service = SandboxService(ctx)
    
    try:
        result = await service.run_single_llm_test(body)
        status = ResponseStatus.SUCCESS if not result.get("error") else {
            "code": "E0501", "msg": result["error"]
        }
        return _create_response(status, int(time.time() * 1000), body.prompt, result)
    
    except ValueError as e:
        return _create_response(ResponseStatus.BAD_REQUEST, int(time.time() * 1000), body.prompt, {})
    
    except Exception as e:
        ctx.log.error(f"[Sandbox] Single LLM test error: {str(e)}")
        return _create_response(ResponseStatus.SERVER_ERROR, int(time.time() * 1000), body.prompt, {})

@router.post("/batch")
async def batch_llm_test(request: Request, body: LLMTestRequest):
    """배치 LLM 테스트"""
    ctx = request.app.state.ctx
    service = SandboxService(ctx)
    
    try:
        result = await service.run_batch_llm_test(body)
        summary = result["summary"]
        msg = f"성공 {summary['successful']} / 실패 {summary['failed']}"
        status = {"code": ResponseStatus.SUCCESS["code"], "msg": msg}
        return _create_response(status, int(time.time() * 1000), body.prompt, result)
    
    except ValueError as e:
        return _create_response(ResponseStatus.BAD_REQUEST, int(time.time() * 1000), body.prompt, {})
    
    except Exception as e:
        ctx.log.error(f"[Sandbox] Batch LLM test error: {str(e)}")
        return _create_response(ResponseStatus.SERVER_ERROR, int(time.time() * 1000), body.prompt, {})
