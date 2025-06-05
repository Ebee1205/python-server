# service/rmq_processor.py
import src.common.common_codes as codes

from src.utils import redis_utils, rabbitmq_utils, websocket_utils
from src.service.scripts import id_generator, chat_service

# 메시지 라우터
async def processor(ctx, msg):
    hd = msg.get("hd")
    msg_type = hd.get('type')
    tid = hd.get("tid")
    sid = hd.get("sid")
    mid = hd.get("mid")
    
    handler = RMQ_PROCESSOR_MAP.get(msg_type)

    if not handler:
        ctx.log.warning(f"[RMQ]     - Unknown processor type: {msg_type}")
        return {"status": "error", "message": f"Unknown type: {msg_type}"}

    return await handler(ctx, msg)

# 핸들러 정의
async def process_ai_chat(ctx, msg):
    """시스템 채팅 메시지 처리"""
    
    # 1. 메시지 파싱 및 검증
    req_msg = chat_service.ChatMessage.from_req_msg(msg)
    is_valid, err_msg = chat_service.validate_message(req_msg)
    
    if not is_valid:
        raise ValueError(f"Invalid message: sid={req_msg.sid}, reason={err_msg}")
    
    try:
        # 2. Redis Stream에 시스템 메시지 기록
        if not await chat_service.SessionService.redis_stream_add_msg(ctx, req_msg, codes.AppStatus.AI_MESSAGE_PROCESSED):
            return None
        
        stream_msg = {
            "tid": req_msg.tid,
            "sid": req_msg.sid,
            "mid": id_generator.generate_mid(),
            "msg": req_msg.msg,
            "type": chat_service.MessageType.CHAT_USER,
            "role": chat_service.MessageRole.USER,
            "userId": req_msg.user_id,
            "status": codes.AppStatus.AI_MESSAGE_PROCESSED,
        }

        # TODO 응답 전송할 websocket이 끊긴 경우 메시지 소비하여 사라지지 않도록... session state/redis stream등 활용하여 보완

        # 3. 세션 상태 업데이트 - AI 응답 전송
        await chat_service.SessionService.redis_update_session_state(ctx, stream_msg, codes.AppStatus.AI_MESSAGE_SENT)
        
        # 4. 성공 응답 반환 - AI 응답 전송
        response = chat_service.ResponseBuilder.build_response(req_msg.sid, req_msg.tid, codes.AppStatus.AI_MESSAGE_SENT )
        await websocket_utils.ws_send_response(ctx, req_msg.sid, response)

        return response
        
    except Exception as e:
        raise ValueError(f"Processing failed: sid={req_msg.sid}, error={e}")

async def handle_rmq_ping(ctx, msg):
    msg = {"status": "ok", "ankoko-to-algo": True, "data": "ping"}
    rabbitmq_utils.rmq_send_response(ctx, "ankoko-to-algo", msg)
    return msg

# 맵핑 테이블...
RMQ_PROCESSOR_MAP = {
    "chat-system": process_ai_chat,
    "router_1": handle_rmq_ping,
}