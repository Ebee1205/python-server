import time
import itertools
from datetime import datetime

from pydantic import BaseModel
from typing import Optional, Dict, Any, List

import psutil

class StatusModel(BaseModel):
    code: str
    msg: Optional[str] = None

class PerformanceModel(BaseModel):
    response_time_ms: float
    memory_usage_mb: float
    cpu_usage_percent: float
    token_count: int
    throughput_tps: float
    timestamp: str

class ModelInfo(BaseModel):
    manager: str
    provider: str

class TransformRequest(BaseModel):
    type: str
    analysis_type: Optional[str] = None
    prompt: str

class LintRequest(BaseModel):
    prompt: str

class SweepTestRequest(BaseModel):
    prompt: str
    sweep: Dict[str, List[Any]]

class LLMTestRequest(BaseModel):
    prompt: str
    analysis_type: str = "sentiment"
    model: str = "llama"
    iterations: int = 1
    concurrent: int = 1
    max_tokens: Optional[int] = 1000
    temperature: Optional[float] = 0.7
    config: Optional[Dict[str, Any]] = {}


class PerformanceMonitor:
    """성능 모니터링을 위한 클래스"""
    
    def __init__(self):
        self.start_time = None
        self.initial_memory = None

    def start_monitoring(self):
        """모니터링 시작"""
        self.start_time = time.time()
        self.initial_memory = psutil.virtual_memory().used / 1024 / 1024

    def stop_monitoring(self) -> Dict[str, float]:
        """모니터링 중지 및 결과 반환"""
        if self.start_time is None:
            raise RuntimeError("Monitoring not started")
            
        end_time = time.time()
        final_memory = psutil.virtual_memory().used / 1024 / 1024
        
        return {
            "response_time_ms": (end_time - self.start_time) * 1000,
            "memory_usage_mb": final_memory - self.initial_memory,
            "cpu_usage_percent": psutil.cpu_percent(interval=None),
            "timestamp": datetime.now().isoformat()
        }

class SandboxService:
    """샌드박스 관련 비즈니스 로직을 처리하는 서비스"""
    
    def __init__(self, ctx):
        self.ctx = ctx
        self.log = ctx.log

    def lint_prompt(self, prompt: str) -> Dict[str, Any]:
        """프롬프트 린트 검사"""
        issues = []
        
        # 기본 검사 규칙들
        if len(prompt) < 10:
            issues.append("프롬프트 길이가 너무 짧음")
            
        if any(p in prompt.lower() for p in ["hi", "hello", "안녕"]):
            issues.append("일반적인 인삿말 포함")
            
        # 추가 검사 규칙들을 여기에 확장 가능
        if not prompt.strip():
            issues.append("빈 프롬프트")
            
        score = max(0, 100 - len(issues) * 20)
        suggestion = "좀 더 구체적인 맥락을 포함해주세요." if issues else "OK"
        
        return {
            "issues": issues,
            "score": score,
            "suggestion": suggestion
        }

    def transform_prompt(self, prompt: str, transform_type: str, analysis_type: Optional[str] = None) -> str:
        """프롬프트 변환"""
        if transform_type == "wrap_in_instruction" and analysis_type:
            return f"You are a helpful assistant. Please {analysis_type} the following text:\n\n{prompt}"
        
        # 다른 변환 타입들을 여기에 추가 가능
        return prompt

    async def run_single_llm_test(self, request: LLMTestRequest) -> Dict[str, Any]:
        """단일 LLM 테스트 실행"""
        llm = self.ctx.llm_manager.get("ops")
        if not llm:
            raise ValueError("LLM manager 'ops' not found")

        monitor = PerformanceMonitor()
        monitor.start_monitoring()

        result_str = ""
        error = None
        
        try:
            chain = llm.get_chain()
            result_str = await chain.ainvoke({"input": request.prompt})
        except Exception as e:
            error = str(e)
            self.log.error(f"[Sandbox] Single LLM test error: {error}")

        metrics = self._create_performance_metrics(
            monitor, request.prompt, result_str
        )

        return {
            "output": result_str if not error else "",
            "metrics": metrics,
            "model_info": ModelInfo(manager="ops", provider="ollama"),
            "config": {
                "max_tokens": request.max_tokens,
                "temperature": request.temperature,
                **(request.config or {})
            },
            "error": error
        }

    async def run_batch_llm_test(self, request: LLMTestRequest) -> Dict[str, Any]:
        """배치 LLM 테스트 실행"""
        llm = self.ctx.llm_manager.get("ops")
        if not llm:
            raise ValueError("LLM manager 'ops' not found")

        results = []
        
        for i in range(request.iterations):
            self.log.info(f"[Sandbox] Running batch test {i+1}/{request.iterations}")
            
            try:
                result = await self.run_single_llm_test(request)
                results.append(result)
            except Exception as e:
                error_result = {
                    "output": "",
                    "metrics": None,
                    "model_info": ModelInfo(manager="ops", provider="ollama"),
                    "config": {
                        "max_tokens": request.max_tokens,
                        "temperature": request.temperature,
                        **(request.config or {})
                    },
                    "error": str(e)
                }
                results.append(error_result)

        return self._create_batch_summary(results)

    async def run_sweep_test(self, prompt: str, sweep_params: Dict[str, List[Any]]) -> List[Dict[str, Any]]:
        """파라미터 스위프 테스트 실행"""
        llm = self.ctx.llm_manager.get("ops")
        if not llm:
            raise ValueError("LLM manager 'ops' not found")

        keys = list(sweep_params.keys())
        combos = list(itertools.product(*[sweep_params[k] for k in keys]))
        results = []

        for combo in combos:
            params = dict(zip(keys, combo))
            self.log.info(f"[Sandbox] Running sweep test with params: {params}")
            
            monitor = PerformanceMonitor()
            monitor.start_monitoring()
            
            result_str = ""
            error = None

            try:
                chain = llm.get_chain()
                result_str = await chain.ainvoke({"input": prompt})
            except Exception as e:
                error = str(e)
                self.log.error(f"[Sandbox] Sweep test error: {error}")

            metrics = self._create_performance_metrics(monitor, prompt, result_str)
            results.append({
                "params": params,
                "metrics": metrics,
                "error": error
            })

        return results

    def _create_performance_metrics(self, monitor: PerformanceMonitor, prompt: str, result: str) -> PerformanceModel:
        """성능 메트릭 생성"""
        metrics_raw = monitor.stop_monitoring()
        token_count = (len(prompt) + len(result)) // 4  # 대략적인 토큰 수 계산
        
        response_time_s = metrics_raw["response_time_ms"] / 1000
        tps = token_count / response_time_s if response_time_s > 0 else 0

        return PerformanceModel(
            response_time_ms=round(metrics_raw["response_time_ms"], 3),
            memory_usage_mb=round(metrics_raw["memory_usage_mb"], 3),
            cpu_usage_percent=metrics_raw["cpu_usage_percent"],
            token_count=token_count,
            throughput_tps=round(tps, 2),
            timestamp=metrics_raw["timestamp"]
        )

    def _create_batch_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """배치 테스트 결과 요약 생성"""
        total = len(results)
        successes = sum(1 for r in results if not r.get("error"))
        fails = total - successes

        # 성공한 결과들만으로 평균 계산
        successful_results = [r for r in results if not r.get("error") and r["metrics"]]
        
        if successful_results:
            avg_metrics = {
                "response_time_ms": round(
                    sum(r["metrics"].response_time_ms for r in successful_results) / len(successful_results), 3
                ),
                "memory_usage_mb": round(
                    sum(r["metrics"].memory_usage_mb for r in successful_results) / len(successful_results), 3
                ),
                "cpu_usage_percent": round(
                    sum(r["metrics"].cpu_usage_percent for r in successful_results) / len(successful_results), 3
                ),
                "token_count": int(
                    sum(r["metrics"].token_count for r in successful_results) / len(successful_results)
                ),
                "throughput_tps": round(
                    sum(r["metrics"].throughput_tps for r in successful_results) / len(successful_results), 2
                )
            }
        else:
            avg_metrics = {
                "response_time_ms": 0,
                "memory_usage_mb": 0,
                "cpu_usage_percent": 0,
                "token_count": 0,
                "throughput_tps": 0
            }

        return {
            "summary": {
                "total": total,
                "successful": successes,
                "failed": fails,
                "average_metrics": avg_metrics
            },
            "individual_results": results
        }
