# admisrc/service/scripts/admin_sandbox_schemas.py

from pydantic import BaseModel
from typing import Optional, Dict, Any, List

class StatusModel(BaseModel):
    code: str
    msg: Optional[str] = None

    class Config:
        validate_by_name = True
        populate_by_name = True

class PerformanceModel(BaseModel):
    # 성능 메트릭
    res_time: float            # 응답 시간 (ms)
    mem_usage: float            # 메모리 사용량 (MB)
    cpu_usage: float            # CPU 사용률 (%)
    gpu_usage: float            # GPU 사용률 (%)

    # 토큰 정보
    in_tokens: int              # 입력 토큰 수
    out_tokens: int             # 출력 토큰 수
    tot_tokens: int             # 총 토큰 수

    # 요청 메타데이터
    max_tokens: int             # max_tokens 설정 값
    temp: float                 # temp 설정 값
    concur_req: int             # 동시 요청 수

    # 타임스탬프
    s_date: int                 # 모니터링 시작 시각
    e_date: int                 # 모니터링 종료 시각
    tps_tokens: float       # 초당 처리 토큰 수

    class Config:
        validate_by_name = True
        populate_by_name = True

class ModelInfo(BaseModel):
    manager: str
    provider: str

    class Config:
        validate_by_name = True
        populate_by_name = True

class TransformRequest(BaseModel):
    event: str
    analysis_type: Optional[str] = None
    prompt: str

    class Config:
        validate_by_name = True
        populate_by_name = True

class LintRequest(BaseModel):
    prompt: str

    class Config:
        validate_by_name = True
        populate_by_name = True

class SweepTestRequest(BaseModel):
    prompt: str
    sweep: Dict[str, List[Any]]

    class Config:
        validate_by_name = True
        populate_by_name = True

class LLMTestRequest(BaseModel):
    prompt: str
    analysis_type: str = "sentiment"
    model: str = "llama"
    iterations: int = 1
    concur_req: int = 1
    max_tokens: int = 1000
    temp: float = 0.7
    cfg: Optional[Dict[str, Any]] = {}

    class Config:
        # 외부에서 camelCase로 들어와도 내부 name(python attr)로 매핑 허용
        populate_by_name = True
        validate_by_name = True

class FeedbackItem(BaseModel):
    score: int
    comment: str

class FeedbackModel(BaseModel):
    coh_flu: FeedbackItem
    relev: FeedbackItem
    factual: FeedbackItem
    helpful: FeedbackItem
    bias_safe: FeedbackItem

class MetricsModel(BaseModel):
    res_time: float
    mem_usage: float
    cpu_usage: float
    gpu_usage: float
    in_tokens: int
    out_tokens: int
    tot_tokens: int
    max_tokens: int
    temp: float
    concur_req: int
    s_date: int
    e_date: int
    tps_tokens: float

class ResultModel(BaseModel):
    output: str
    metrics: MetricsModel
    cfg: Dict[str, int | float]
    error: Optional[str] = None

class DocumentModel(BaseModel):
    status: str
    tid: str
    event: str
    task_id: str
    req: Dict
    res: ResultModel
    feedback: Optional[FeedbackModel] = None
