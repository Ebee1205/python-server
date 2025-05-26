# routes/session_router.py

from fastapi import APIRouter, Request, Body
from typing import Annotated
import time, json

from src.service.scripts import session_service
from src.utils import redis_utils

router = APIRouter(prefix="/api/session", tags=["Session"])

@router.post("/connect")
async def connect_session(
    request: Request,
    userId: Annotated[str, Body(embed=True)],
):
    sid = session_service.generate_sid()
    now = int(time.time() * 1000)

    session = {
        "sid": sid,
        "userId": userId,
        "createdAt": now,
        "lastActiveAt": now,
        "type": "img",  # 기본 세션 타입. 필요 시 클라이언트에서 받아도 됨
        "state": {
            "status": "active"
        }
    }

    redis_utils.redis_set(request.app.state.ctx, f"session:{sid}", json.dumps(session), expire_sec=3600)

    return {
        "sid": sid,
        "createdAt": now,
        "status": "active"
    }