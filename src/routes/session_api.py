# routes/session_router.py

from fastapi import APIRouter, Request, Body
from typing import Annotated
import time, orjson

from src.service.scripts import session_service
from src.utils import redis_utils

router = APIRouter(prefix="/v1/session", tags=["Session"])

# TODO errCode와 msg 맞춰서 수정하기. 지금은 하드코딩 되어잇음
# TODO status에 대한 commonCode 있는게 좋긴 할듯

@router.post("/connect")
async def connect_session(
    request: Request,
    userId: Annotated[str, Body(embed=True)],
):
    sid = session_service.generate_sid()
    tid = int(time.time() * 1000)

    # Redis 키
    redis_key = f"session:{sid}"

    fields = {
        "sid": sid,
        "userId": userId,
        "device": "web",
        "chatCount": 0,
        # "lastChatId": None, 
        # "lang": None,
        # "modelId": None,
        "cDate": tid,
        "uDate": tid,
        "lastAcc": tid,
        "status": "session_created",
        "ttl": 86400
    }

    await redis_utils.redis_hset_multi(request.app.state.ctx, redis_key, fields)

    response = {
        "hd": {
            "type": "system",
            "tid": tid
        },
        "dt": {
            "sid": sid,
            "status": "session_created",
            "code": "S00001",
            "msg": "Successed"
        }
    }

    return response


@router.post("/disconnect")
async def disconnect_session(
    request: Request,
    sid: Annotated[str, Body(embed=True)],
    userId: Annotated[str, Body(embed=True)]
):
    tid = int(time.time() * 1000)
    
    # Redis 키
    redis_key = f"session:{sid}"

    # 상태 업데이트 (평평한 구조 그대로)
    fields = {
        "status": "session_ended",
        "state": "ended",
        "uDate": tid,
        "lastAcc": tid
    }

    await redis_utils.redis_hset_multi(request.app.state.ctx, redis_key, fields)

    response = {
        "hd": {
            "type": "system",
            "event": "session_ended",
            "tid": tid
        },
        "dt": {
            "sid": sid,
            "userId": userId,
            "msg": "Session ended by user",
            "code": "S00002",
            "status": "success"
        }
    }

    return response