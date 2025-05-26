# service/ws_processor.py

import time
from src.utils import redis_utils

async def processor(ctx, websocket, msg):
    msg_type = msg.get("type")
    handler = MAP.get(msg_type)

    if not handler:
        ctx.log.warning(f"[WS] Unknown message type: {msg_type}")
        return {"status": "error", "message": f"Unknown type: {msg_type}"}

    return await handler(ctx, websocket, msg)


# 핸들러 정의 예시
async def handle_ping(ctx, websocket, msg):
    return {"status": "ok", "type": "pong", "tid": msg.get("tid")}

async def process_chat_message(ctx, websocket, message):
    stream_key = "chat_stream"
    session_id = message["session_id"]
    user_id = message["user_id"]
    text = message["text"]
    tid = message.get("tid") or str(int(time.time() * 1000))  # 트랜잭션 ID
    hash_key = f"chat:session:{session_id}"
    msg_id = str(int(time.time()))


   # AI 생성 중 알림 보내기
   # TODO 관련 로그 추가
   # TODO status 이렇게 하나하나 박지말고 통합하고 싶긴한데...
    await websocket.send_json({
        "status": "processing",
        "msg_id": msg_id,
        "session_id": session_id,
        "message": "🤖 AI 응답 생성 중..."
    })

    # 1. Redis Stream 기록
    stream_result = await redis_utils.redis_stream_add(ctx, stream_key, {
        "session_id": session_id,
        "user_id": user_id,
        "text": text,
        "type": "user",
        "msg_id": msg_id,
        "tid": tid,
        "state": "pending"
    })

    if not stream_result:
        raise RuntimeError("❌ Stream 기록 실패")

    # 2. Redis Hash 상태 업데이트
    hash_update = await redis_utils.redis_hset(ctx, hash_key, "state", "waiting_ai")
    hash_time = await redis_utils.redis_hset(ctx, hash_key, "last_updated", tid)

    if not hash_update:
        ctx.log.warning(f"⚠️ 상태 업데이트 실패 - session: {session_id}")

    return {
        "status": "S0000",
        "msg_id": msg_id,
        "tid": tid,
        "session_id": session_id,
        "user_id": user_id,
        "state": "processed_msg"
    }


# 맵핑 테이블
MAP = {
    "ping": handle_ping,
    "chat": process_chat_message
}
