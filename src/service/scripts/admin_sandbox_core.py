import time
import itertools
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

import psutil
import pynvml

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

class PerformanceMonitor:
    def __init__(self):
        pynvml.nvmlInit()
        self.start_time = None
        self.initial_memory = None
        self.s_date = None

    def start_monitoring(self):
        self.start_time = time.time()
        self.s_date = int(time.time() * 1000)
        self.initial_memory = psutil.virtual_memory().used / (1024 * 1024)

    def stop_monitoring(self) -> dict:
        if self.start_time is None:
            raise RuntimeError('Monitoring not started')
        end_time = time.time()
        e_date = int(time.time() * 1000)
        final_mem = psutil.virtual_memory().used / (1024 * 1024)
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        util = pynvml.nvmlDeviceGetUtilizationRates(handle)
        return {
            'res_time': (end_time - self.start_time) * 1000,
            'mem_usage': final_mem - self.initial_memory,
            'cpu_usage': psutil.cpu_percent(interval=None),
            'gpu_usage': util.gpu,
            's_date': self.s_date,
            'e_date': e_date
        }

class SandboxService:
    def __init__(self, ctx):
        self.ctx = ctx
        self.log = ctx.log

    def lint_prompt(self, prompt: str) -> Dict[str, Any]:
        issues = []
        if len(prompt) < 10:
            issues.append('too short')
        if any(g in prompt.lower() for g in ['hi', 'hello', '안녕']):
            issues.append('greeting included')
        if not prompt.strip():
            issues.append('empty prompt')
        score = max(0, 100 - len(issues) * 20)
        suggestion = 'add more context' if issues else 'OK'
        return {'issues': issues, 'score': score, 'suggestion': suggestion}

    def transform_prompt(self, prompt: str, mode: str, analysis_type: Optional[str] = None) -> str:
        if mode == 'wrap_in_instruction' and analysis_type:
            return f'You are an assistant. Please {analysis_type}: {prompt}'
        return prompt

    async def run_single(self, req: LLMTestRequest) -> Dict[str, Any]:
        llm = self.ctx.llm_manager.get('ops')
        if not llm:
            raise ValueError("LLM manager 'ops' missing")
        monitor = PerformanceMonitor()
        monitor.start_monitoring()
        out, err = '', None
        try:
            chain = llm.get_chain()
            out = await chain.ainvoke({'input': req.prompt})
        except Exception as e:
            err = str(e)
            self.log.error(f'error: {err}')
        raw = monitor.stop_monitoring()
        in_tok = len(req.prompt) // 4
        out_tok = len(out) // 4
        tot_tok = in_tok + out_tok
        dur_sec = raw['res_time'] / 1000
        tps = tot_tok / dur_sec if dur_sec > 0 else 0
        metrics = PerformanceModel(
            **raw,
            in_tokens=in_tok,
            out_tokens=out_tok,
            tot_tokens=tot_tok,
            max_tokens=req.max_tokens,
            temp=req.temp,
            concur_req=req.concur_req,
            tps_tokens=round(tps, 2)
        )
        return {
            'output': out if not err else '',
            'metrics': metrics.dict(by_alias=True),
            'cfg': {
                'max_tokens': req.max_tokens,
                'temp': req.temp,
                'concur_req': req.concur_req
            },
            'error': err
        }

    async def run_batch(self, req: LLMTestRequest) -> Dict[str, Any]:
        results = []
        for i in range(req.iterations):
            self.log.info(f'batch {i+1}/{req.iterations}')
            res = await self.run_single(req)
            results.append(res)
        total = len(results)
        succ = sum(1 for r in results if not r.get('error'))
        ok = [r for r in results if not r.get('error')]
        avg = {}
        if ok:
            count = len(ok)
            avg = {k: round(sum(r['metrics'][k] for r in ok)/count, 3) for k in ['res_time','mem_usage','cpu_usage','tps_tokens']}
            avg['tot_tokens'] = int(sum(r['metrics']['tot_tokens'] for r in ok)/count)
        return {'summary': {'total': total, 'successful': succ, 'failed': total-succ, 'average': avg}, 'individual': results}

    async def run_sweep(self, req: SweepTestRequest) -> List[Dict[str, Any]]:
        llm = self.ctx.llm_manager.get('ops')
        combos = list(itertools.product(*req.sweep.values()))
        out = []
        for params in combos:
            pmap = dict(zip(req.sweep.keys(), params))
            self.log.info(f'sweep {pmap}')
            monitor = PerformanceMonitor()
            monitor.start_monitoring()
            res_str, err = '', None
            try:
                chain = llm.get_chain()
                res_str = await chain.ainvoke({'input': req.prompt})
            except Exception as e:
                err = str(e)
            raw = monitor.stop_monitoring()
            in_tok = len(req.prompt)//4
            out_tok = len(res_str)//4
            tot_tok = in_tok+out_tok
            dur = raw['res_time']/1000
            tps = tot_tok/dur if dur>0 else 0
            metrics = PerformanceModel(
                **raw,
                in_tokens=in_tok,
                out_tokens=out_tok,
                tot_tokens=tot_tok,
                max_tokens=raw.get('max_tokens', 0),
                temp=raw.get('temp', 0.0),
                concur_req=raw.get('concur_req', 0),
                tps_tokens=round(tps, 2)
            )
            out.append({'params': pmap, 'metrics': metrics.dict(by_alias=True), 'error': err})
        return out
