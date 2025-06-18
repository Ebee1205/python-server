from typing import Literal
from datetime import datetime
from fastapi import APIRouter, Query, Body
from src.service.scripts.admin_sandbox_schemas import (
    DocumentModel, ResultModel, MetricsModel, FeedbackModel, FeedbackItem, DocumentModel
)

router = APIRouter(prefix="/v1/admin/sandbox", tags=["Sandbox"])

# === Document CRUD ===

@router.post("/docs", response_model=DocumentModel)
async def create_doc(
    document: DocumentModel = Body(..., description="생성할 문서 객체")
):
    # 실제 저장은 하지 않고 그대로 반환 (mock)
    return document

@router.get("/docs", response_model=DocumentModel)
async def read_doc(task_id: str = Query(..., description="Task ID")):
    return create_mock_document(task_id)

@router.put("/docs", response_model=DocumentModel)
async def update_doc(task_id: str = Query(..., description="Task ID")):
    return create_mock_document(task_id)

@router.delete("/docs", response_model=DocumentModel)
async def delete_doc(task_id: str = Query(..., description="Task ID")):
    return create_mock_document(task_id)

# === Stats Summary ===

@router.get("/stats")
async def read_stats(
    type: Literal["batch", "single", "all"] = Query(..., description="통계 유형")
):
    if type == "batch":
        summary = {
            "total": 1,
            "successful": 1,
            "failed": 0,
            "average": {
                "res_time": 58469.048,
                "mem_usage": 145.199,
                "cpu_usage": 49.9,
                "tps_tokens": 11.56,
                "tot_tokens": 676
            }
        }
    elif type == "single":
        summary = {
            "total": 1,
            "successful": 1,
            "failed": 0,
            "average": {
                "res_time": 66419.884,
                "mem_usage": 21.082,
                "cpu_usage": 55.3,
                "tps_tokens": 2.65,
                "tot_tokens": 176
            }
        }
    else:  # all
        summary = {
            "total": 2,
            "successful": 2,
            "failed": 0,
            "average": {
                "res_time": (58469.048 + 66419.884) / 2,
                "mem_usage": (145.199 + 21.082) / 2,
                "cpu_usage": (49.9 + 55.3) / 2,
                "tps_tokens": (11.56 + 2.65) / 2,
                "tot_tokens": (676 + 176) / 2
            }
        }
    return summary

# === 목데이터 생성 유틸리티 ===

def create_mock_document(task_id: str) -> DocumentModel:
    now = int(datetime.now().timestamp() * 1000)

    metrics = MetricsModel(
        res_time=12345.67,
        mem_usage=12.3,
        cpu_usage=45.6,
        gpu_usage=0.0,
        in_tokens=20,
        out_tokens=100,
        tot_tokens=120,
        max_tokens=500,
        temp=0.7,
        concur_req=1,
        s_date=now - 12345,
        e_date=now,
        tps_tokens=9.7
    )

    result = ResultModel(
        output="이것은 블랙홀에 대한 간단한 설명입니다.",
        metrics=metrics,
        cfg={
            "max_tokens": 500,
            "temp": 0.7,
            "concur_req": 1
        },
        error=None
    )

    feedback = FeedbackModel(
        coh_flu=FeedbackItem(score=5, comment="매우 자연스러움"),
        relev=FeedbackItem(score=4, comment="관련성 있음"),
        factual=FeedbackItem(score=3, comment="사실성 중간"),
        helpful=FeedbackItem(score=5, comment="매우 도움됨"),
        bias_safe=FeedbackItem(score=5, comment="편향 없음")
    )

    return DocumentModel(
        status="success",
        tid=str(now),
        event="sandbox-result",
        task_id=task_id,
        req={
            "prompt": "블랙홀에 대해 간단히 설명해줘",
            "analysis_type": "summary",
            "model": "llama",
            "iterations": 1,
            "concur_req": 1,
            "max_tokens": 500,
            "temp": 0.7,
            "cfg": {}
        },
        res=result,
        feedback=feedback
    )
