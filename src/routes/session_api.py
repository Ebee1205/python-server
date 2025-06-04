# routes/session_router.py

from fastapi import APIRouter, Request, Body
from typing import Annotated
import time

import src.common.common_codes as codes
from src.service.scripts import session_service
from src.utils import redis_utils

router = APIRouter(prefix="/v1/session", tags=["Session"])

# TODO errCode와 msg 맞춰서 수정하기. 지금은 하드코딩 되어잇음

# /v1/session/create
@router.post("/create")
async def connect_session(
    request: Request,
    userId: Annotated[str, Body(embed=True)],
):
    sid = session_service.generate_sid()
    tid = int(time.time() * 1000)

    # Redis 키
    redis_key = f"session:{sid}"

    # Redis 해쉬맵에 상태 업데이트
    fields = {
        "sid": sid,
        "userId": userId,
        "device": "web", # TODO device정보는 클라이언트에서 보내줘야할듯?
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

# /v1/session/delete
@router.post("/delete")
async def disconnect_session(
    request: Request,
    sid: Annotated[str, Body(embed=True)],
    userId: Annotated[str, Body(embed=True)]
):
    tid = int(time.time() * 1000)
    
    # Redis 키
    redis_key = f"session:{sid}"

    # Redis 해쉬맵에 상태 업데이트
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
            "userId": userId
            # 필요한 유저 정보 추가...
        },
        "status": codes.AppStatus.SESSION_ENDED,
        **codes.ResponseStatus.SUCCESS
    }

    return response