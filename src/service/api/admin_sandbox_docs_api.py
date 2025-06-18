# src/routes/admin_sandbox_api.py

from fastapi import APIRouter, Query
from typing import Literal

router = APIRouter(prefix="/v1/admin/sandbox", tags=["Sandbox"])

# 1) Document CRUD (Mock)
@router.post("/docs")
async def create_doc(task_id: str = Query(..., description="Task ID")):
    # 실제 저장 로직은 없음
    return {"status": "CREATED", "task_id": task_id}

@router.get("/docs")
async def read_doc(task_id: str = Query(..., description="Task ID")):
    # Mock 문서 데이터 예시
    return {
        "prompt": "batch prompt 테스트에 대해 설명해주세요.",
        "analysis_type": "sentiment",
        "model": "llama",
        "iterations": 1,
        "concurrent": 1,
        "max_tokens": 512,
        "temperature": 0.7,
        "additional_params": {"top_p": 0.9}
    }

@router.put("/docs")
async def update_doc(task_id: str = Query(..., description="Task ID")):
    # 실제 수정 로직은 없음
    return {"status": "UPDATED", "task_id": task_id}

@router.delete("/docs")
async def delete_doc(task_id: str = Query(..., description="Task ID")):
    # 실제 삭제 로직은 없음
    return {"status": "DELETED", "task_id": task_id}

# 2) Stats 조회 (Mock Summary)
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
