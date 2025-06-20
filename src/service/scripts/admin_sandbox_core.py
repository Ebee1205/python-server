import time
import uuid
import itertools
import psutil
import pynvml

from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from src.service.scripts.admin_sandbox_schemas import (
    ResultModel,
    MetricsModel,
    DocumentModel,
    LLMTestRequest,
    SweepTestRequest,
    TransformRequest,
    LintRequest,
    StatusModel
)

class PerformanceMonitor:
    def __init__(self):
        pynvml.nvmlInit()
        self.start_time = None
        self.initial_memory = None
        self.s_date = None

    def start_monitoring(self):
        self.start_time = time.time()
        self.s_date = int(self.start_time * 1000)
        self.initial_memory = psutil.virtual_memory().used / (1024 * 1024)

    def stop_monitoring(self) -> dict:
        if self.start_time is None:
            raise RuntimeError('Monitoring not started')
        end_time = time.time()
        e_date = int(end_time * 1000)
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

    async def run_single(self, req: LLMTestRequest) -> DocumentModel:
        llm = self.ctx.llm_manager.get('ops')
        if not llm:
            raise ValueError("LLM manager 'ops' missing")

        monitor = PerformanceMonitor()
        monitor.start_monitoring()

        out, err = '', None
        try:
            prompt = self.transform_prompt(req.prompt, 'wrap_in_instruction', req.analysis_type)
            chain = llm.get_chain()
            out = await chain.ainvoke({'input': prompt})
        except Exception as e:
            err = str(e)
            self.log.error(f'[LLM] error: {err}')

        raw = monitor.stop_monitoring()
        in_tok = len(req.prompt) // 4
        out_tok = len(out) // 4
        tot_tok = in_tok + out_tok
        dur_sec = raw['res_time'] / 1000
        tps = tot_tok / dur_sec if dur_sec > 0 else 0

        metrics = MetricsModel(
            **raw,
            in_tokens=in_tok,
            out_tokens=out_tok,
            tot_tokens=tot_tok,
            max_tokens=req.max_tokens,
            temp=req.temp,
            concur_req=req.concur_req,
            tps_tokens=round(tps, 2)
        )

        result = ResultModel(
            output=out if not err else '',
            metrics=metrics,
            cfg={
                "max_tokens": req.max_tokens,
                "temp": req.temp,
                "concur_req": req.concur_req
            },
            error=err
        )

        doc = DocumentModel(
            status="success",
            tid=str(int(time.time() * 1000)),
            event="sandbox-result",
            task_id=str(uuid.uuid4()),
            req=req.dict(),
            res=result,
            feedback=None
        )
        return doc

    async def run_batch(self, req: LLMTestRequest) -> Dict[str, Any]:
        results = []
        for i in range(req.iterations):
            self.log.info(f'batch {i+1}/{req.iterations}')
            res = await self.run_single(req)
            results.append(res)
        total = len(results)
        ok = [r for r in results if r.res.error is None]
        avg = {}
        if ok:
            count = len(ok)
            avg = {
                k: round(sum(getattr(r.res.metrics, k) for r in ok) / count, 3)
                for k in ['res_time', 'mem_usage', 'cpu_usage', 'tps_tokens']
            }
            avg['tot_tokens'] = int(sum(r.res.metrics.tot_tokens for r in ok) / count)

        return {
            'summary': {
                'total': total,
                'successful': len(ok),
                'failed': total - len(ok),
                'average': avg
            },
            'list': [r.dict() for r in results]
        }

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
            in_tok = len(req.prompt) // 4
            out_tok = len(res_str) // 4
            tot_tok = in_tok + out_tok
            dur = raw['res_time'] / 1000
            tps = tot_tok / dur if dur > 0 else 0

            metrics = MetricsModel(
                **raw,
                in_tokens=in_tok,
                out_tokens=out_tok,
                tot_tokens=tot_tok,
                max_tokens=req.max_tokens,
                temp=req.temp,
                concur_req=req.concur_req,
                tps_tokens=round(tps, 2)
            )

            out.append({
                'params': pmap,
                'metrics': metrics.dict(),
                'error': err
            })

        return out
