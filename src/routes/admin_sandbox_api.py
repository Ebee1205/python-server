from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
import time, psutil, uuid

router = APIRouter(prefix="/v1/admin/sandbox", tags=["Sandbox"])

# -------------------------
# Request/Response 모델 정의
# -------------------------
class PatternTestRequest(BaseModel):
    code: str

class LLMTestRequest(BaseModel):
    prompt: str
    analysis_type: str = "sentiment"  # sentiment, summary, keywords, classification, creative
    model: str = "llama"
    iterations: int = 1
    concurrent: int = 1
    max_tokens: Optional[int] = 1000
    temperature: Optional[float] = 0.7
    additional_params: Optional[Dict[str, Any]] = {}

class PerformanceMetrics(BaseModel):
    response_time_ms: float
    memory_usage_mb: float
    cpu_usage_percent: float
    token_count: int
    throughput_tps: float
    success: bool
    error_message: Optional[str] = None
    timestamp: str

class LLMTestResponse(BaseModel):
    success: bool
    request_id: str
    input_prompt: str
    output_text: str
    metrics: PerformanceMetrics
    model_info: Dict[str, Any]
    test_config: Dict[str, Any]

class BatchTestResponse(BaseModel):
    success: bool
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_metrics: PerformanceMetrics
    individual_results: List[LLMTestResponse]
    summary: Dict[str, Any]

# -------------------------
# 성능 모니터링 클래스
# -------------------------
class PerformanceMonitor:
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.initial_memory = None
        self.initial_cpu = None

    def start_monitoring(self):
        self.start_time = time.time()
        self.initial_memory = psutil.virtual_memory().used / 1024 / 1024  # MB
        self.initial_cpu = psutil.cpu_percent(interval=None)

    def stop_monitoring(self) -> Dict[str, float]:
        self.end_time = time.time()
        final_memory = psutil.virtual_memory().used / 1024 / 1024  # MB
        final_cpu = psutil.cpu_percent(interval=None)

        return {
            "response_time_ms": (self.end_time - self.start_time) * 1000,
            "memory_usage_mb": final_memory - self.initial_memory,
            "cpu_usage_percent": final_cpu,
            "timestamp": datetime.now().isoformat()
        }

# -------------------------
# 샌드박스용 LLM 테스트 엔드포인트
# -------------------------
@router.post("/llama")
async def translate_pattern(request: Request, body: PatternTestRequest):
    """
    사용자 JS draw 함수를 받아 patterns[] 항목 포맷으로 변환 및 성능 측정
    """
    ctx = request.app.state.ctx
    llm = ctx.llm_manager.get("sandbox")
    if not llm:
        return {"success": False, "error": "LLM manager 'sandbox' not found"}

    monitor = PerformanceMonitor()
    monitor.start_monitoring()
    result_str = ""
    error = None

    try:
        chain = llm.get_chain()
        result_str = await chain.ainvoke({"input": body.code})
    except Exception as e:
        error = str(e)
        ctx.log.error(f"[Sandbox] Error during LLM pattern conversion: {error}")

    metrics_raw = monitor.stop_monitoring()
    input_len = len(body.code)
    output_len = len(result_str)
    token_count = (input_len + output_len) // 4
    tps = token_count / (metrics_raw["response_time_ms"] / 1000) if metrics_raw["response_time_ms"] > 0 else 0

    metrics = PerformanceMetrics(
        response_time_ms=round(metrics_raw["response_time_ms"], 3),
        memory_usage_mb=round(metrics_raw["memory_usage_mb"], 3),
        cpu_usage_percent=metrics_raw["cpu_usage_percent"],
        token_count=token_count,
        throughput_tps=round(tps, 2),
        success=error is None,
        error_message=error,
        timestamp=metrics_raw["timestamp"]
    )

    return LLMTestResponse(
        success=error is None,
        request_id=str(uuid.uuid4()),
        input_prompt=body.code,
        output_text=result_str if not error else "",
        metrics=metrics,
        model_info={"manager": "sandbox", "provider": "ollama"},
        test_config={"max_tokens": 1000, "temperature": 0.7}
    )
