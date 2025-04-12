# 웹소켓 기본 예제
# 웹소켓 핸들러를 사용하여 클라이언트와 서버 간의 메시지를 주고받는 예제임.
# routes/websocket_basic.py

from fastapi import APIRouter, WebSocket

import time
from src.utils import redis_utils

router = APIRouter()

# TODO processor 지정하기
@router.websocket("/ws")
async def websocket_basic(websocket: WebSocket):
    ctx = websocket.app.state.ctx
    await ctx.ws_handler.connect(websocket)
    await ctx.ws_handler.receive_and_respond(
        websocket,
        mode="basic",
        processor=process_chat_message  # ✅ processor 함수 지정
    )

async def process_chat_message(websocket, message):
    ctx = websocket.app.state.ctx
    
    stream_key = "chat_stream"
    session_id = message["session_id"]
    user_id = message["user_id"]
    text = message["text"]
    tid = message.get("tid") or str(int(time.time() * 1000))  # 트랜잭션 ID
    hash_key = f"chat:session:{session_id}"
    msg_id = str(int(time.time()))


   # AI 생성 중 알림 보내기
   # TODO 관련 로그 추가
    await websocket.send_json({
        "status": "processing",
        "msg_id": msg_id,
        "session_id": session_id,
        "message": "🤖 AI 응답을 생성 중입니다..."
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

# TODO
# msg 처리흐름: 웹소켓으로 수신, redis Stream에 기록, redis Hash에 응답 상태 기록, rabbitmq 큐에 메시지 전송
# msg 수신흐름: AI서버가 rabbitmq에 응답 전송, redis Stream에 기록, redis Hash에 응답상태 기록, 웹소켓으로 전송
# 구현 우선순위: 웹소켓, redis stream, rabbitmq, 상태관리는 마지막에 추가


# 1차적인 msg processor 구조는 

# 1. message 수신
# 2. set_redis_stream(session, user, msg)
# 3. set_state_getmeg(asfd)
# 4. send_msg(rmq, msg)

# 5. res = get_msq(rmq)
# 6. set_redis_stream(session, ai, res)
# 7. set_state_sentmsg(res)
# 8. return res

# TODO 그럼만약에 sendres로 웹소켓으로 response 보낼때 유실이 일어나면? redis에 기록된 내용 다시 가져오려면?
# gpt 답변 참조

# processor를 api로 가져와서 .run() 으로 set_session msg_process 등등 
# 파사드패턴?으로 자동 play시키면 flow ui구현가능할듯