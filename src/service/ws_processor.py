# service/ws_processor.py

import time

import src.common.common_codes as codes

from src.utils import redis_utils
from src.utils import rabbitmq_utils
from src.service.scripts import session_service

async def processor(ctx, websocket, msg):
    hd = msg.get("hd")
    msg_type = hd['type']

    handler = MAP.get(msg_type)
    if not handler:
        ctx.log.warning(f"[WS] Unknown message type: {msg_type}")
        return {"status": "error", "message": f"Unknown type: {msg_type}"}

    return await handler(ctx, websocket, msg)

# operation handler defination sample
async def handle_ping(ctx, websocket, msg):
    return {"status": "ok", "type": "pong", "tid": msg.get("tid")}

# TODO session의 status와 그냥 req/res의 error code, state 구분하기
async def process_user_chat(ctx, websocket, msg):
    hd = msg.get("hd")
    dt = msg.get("dt")

    role = hd.get("role")
    msg_type = hd.get("type")
    sid = hd.get("sid")
    user_id = hd.get("userId")
    mid = hd.get("msgId")
    tid = hd.get("tid")

    text = dt.get("msg")
    
    # 방어로직 - vlidation check
    if role != "user" or msg_type != "chat-user":
        ctx.log.warning(f"[WS] wrong packet - role={role}, type={msg_type}")
        return
    if not sid or not user_id or not text:
        ctx.log.warning(f"[WS] invalid data: sid={sid}, userId={user_id}, text={text}")
        return
    
    # 2. Redis Stream에 사용자 메시지 기록
    stream_key = "chat_stream"
    stream_msg = {
        "tid": tid,
        "sid": sid,
        "userId": user_id,
        "text": text,
        "type": "user",
        "mid": session_service.generate_mid(),
        "status": codes.AppStatus.USER_MESSAGE_RECEIVED,
    }
    

    await websocket.send_json({
        "hd": {
            "type": "system",
            "tid": tid
        },
        "dt": {
            "sid": sid,
            "msgId": session_service.generate_mid(),
            "status": codes.AppStatus.AI_PROCESSING_STARTED,
            "message": "AI 응답 생성 중..."
        }
    })

    stream_result = await redis_utils.redis_stream_add(ctx, stream_key, stream_msg)
    await rabbitmq_utils.rmq_send_response(ctx, "ankoko-to-algo", stream_msg)

    if not stream_result:
        ctx.log.error(f"Redis stream 기록 실패: sid={sid}, mid={mid}")
        return

    # 3. Redis 상태 업데이트
    hash_key = f"chat:session:{sid}"
    await redis_utils.redis_hset_multi(ctx, hash_key, {
        "state": codes.AppStatus.AI_MESSAGE_SENT,
        "last_updated": tid
    })
    await redis_utils.redis_hincrby(ctx, hash_key, "chatCount", 1)

    ctx.log.debug(f"[WS] 사용자 메시지 처리 완료: sid={sid}, mid={mid}")

    return {
        "mid": mid,
        "tid": tid,
        "sid": sid,
        "userId": user_id,
        "status": codes.AppStatus.AI_MESSAGE_SENT
    }

async def process_ai_chat(ctx, websocket, msg):
    hd = msg.get("hd")
    dt = msg.get("dt")
    role = hd['role']
    
    return 

# 맵핑 테이블
MAP = {
    "ping": handle_ping,
    "chat-user": process_user_chat,
    "chat-ai": process_ai_chat
}

