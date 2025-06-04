# routes/session_router.py

from fastapi import APIRouter, Request, Body
from typing import Annotated
import time

import src.common.common_codes as codes
from src.service.scripts import session_service
from src.utils import redis_utils

router = APIRouter(prefix="/v1/session", tags=["Session"])

# TODO errCode와 msg 맞춰서 수정하기. 지금은 하드코딩 되어잇음

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
        "status": codes.AppStatus.SESSION_CREATED,
        "cDate": tid,
        "uDate": tid,
        "lastAcc": tid,
        "ttl": 86400
    }

    await redis_utils.redis_hset_multi(request.app.state.ctx, redis_key, fields)

    response = {
        "tid": tid,
        "sid": sid,
        "status": codes.AppStatus.SESSION_CREATED,
        **codes.ResponseStatus.SUCCESS,
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
        "status": codes.AppStatus.SESSION_ENDED,
        "uDate": tid,
        "lastAcc": tid
    }

    await redis_utils.redis_hset_multi(request.app.state.ctx, redis_key, fields)

    response = {
        "tid": tid,
        "sid": sid,
        "user": {
            "userId": userId,
        },
        "status": codes.AppStatus.SESSION_ENDED,
        **codes.ResponseStatus.SUCCESS
    }

    return response