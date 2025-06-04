# service/ws_processor.py
import src.common.common_codes as codes

from src.utils import redis_utils
from src.utils import rabbitmq_utils
from src.service.scripts import session_service, id_generator

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

# 메인 처리 함수
async def process_user_chat(ctx, websocket, msg):
    """사용자 채팅 메시지 처리"""
    
    # 1. 메시지 파싱 및 검증
    chat_msg = session_service.ChatMessage.from_websocket_msg(msg)
    is_valid, err_msg = session_service.validate_message(chat_msg)
    
    if not is_valid:
        raise ValueError(f"Invalid message: sid={chat_msg.sid}, reason={err_msg}")
    
    try:
        # 2. Redis Stream에 사용자 메시지 기록
        if not await session_service.SessionService.add_user_message(ctx, chat_msg):
            return None
        
        # 3. AI 서버에 메시지 전송
        stream_msg = {
            "tid": chat_msg.tid,
            "sid": chat_msg.sid,
            "userId": chat_msg.user_id,
            "text": chat_msg.text,
            "type": "user",
            "mid": id_generator.generate_mid(),
            "status": codes.AppStatus.USER_MESSAGE_RECEIVED,
        }
        await rabbitmq_utils.rmq_send_response(ctx, "ankoko-to-algo", stream_msg)
        
        # 4. 세션 상태 업데이트 - AI 응답 생성중
        await session_service.SessionService.update_session_state(
            ctx, chat_msg.sid, chat_msg.tid, codes.AppStatus.AI_PROCESSING_STARTED
        )
        
        # 5. 성공 응답 반환 - AI 응답 생성중
        response = session_service.ResponseBuilder.build_response(chat_msg.sid, chat_msg.tid, codes.ResponseStatus.SERVER_ERROR )
        return response
        
    except Exception as e:
        raise ValueError(f"Processing failed: sid={chat_msg.sid}, error={e}")

# 맵핑 테이블
MAP = {
    "ping": handle_ping,
    "chat-user": process_user_chat
}

