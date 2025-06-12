from service.scripts.chat import chat_service
import src.common.common_codes as codes
from src.utils import redis_utils
from src.utils import rabbitmq_utils
from src.service.scripts import id_generator

async def processor(ctx, websocket, msg):
    hd = msg.get("hd")
    msg_type = hd.get('type')
    tid = hd.get("tid")
    sid = hd.get("sid")
    mid = hd.get("mid")

    handler = MAP.get(msg_type)
    if not handler:
        ctx.log.warning(f"[WS]     - Unknown message type: {msg_type}, tid={tid}, sid={sid}, mid={mid}")
        return {"status": "error", "message": f"Unknown type: {msg_type}"}

    return await handler(ctx, websocket, msg)

async def handle_ping(ctx, websocket, msg):
    sid = msg.get("hd", {}).get("sid")
    ctx.log.debug(f"[WS]     >> Ping request received: sid={sid}")
    return {"status": "ok", "type": "pong", "tid": msg.get("tid")}

async def process_user_chat(ctx, websocket, msg):
    """사용자 채팅 메시지 처리"""
    ctx.log.debug("[WS]     >> Start processing user chat message")

    # 1. 메시지 파싱 및 검증
    req_msg = chat_service.ChatMessage.from_req_msg(msg)
    is_valid, err_msg = chat_service.validate_message(req_msg)

    if not is_valid:
        ctx.log.warning(f"[WS]     - Invalid message format: sid={req_msg.sid}, reason={err_msg}")
        raise ValueError(f"Invalid message: sid={req_msg.sid}, reason={err_msg}")

    try:
        # 2. Redis Stream에 사용자 메시지 기록
        await chat_service.SessionService.redis_stream_add_msg(ctx, req_msg, codes.AppStatus.USER_MESSAGE_RECEIVED)

        # 3. AI 서버에 메시지 전송
        stream_msg = {
            "tid": req_msg.tid,
            "sid": req_msg.sid,
            "mid": id_generator.generate_mid(),
            "msg": req_msg.msg,
            "type": chat_service.MessageType.CHAT_USER,
            "role": chat_service.MessageRole.USER,
            "userId": req_msg.user_id,
            "status": codes.AppStatus.USER_MESSAGE_RECEIVED,
        }

        await rabbitmq_utils.rmq_send_response(ctx, "ankoko-to-algo", {
            "hd": {
                "tid": req_msg.tid,
                "sid": req_msg.sid,
                "mid": req_msg.mid,
                "type": chat_service.MessageType.CHAT_USER,
                "role": chat_service.MessageRole.USER,
                "userId": req_msg.user_id,
            },
            "dt": {
                "msg": req_msg.msg,
                "status": codes.AppStatus.USER_MESSAGE_RECEIVED
            }
        })

        # 4. 세션 상태 업데이트 - AI 응답 생성중
        await chat_service.SessionService.redis_update_session_state(ctx, stream_msg, codes.AppStatus.AI_PROCESSING_STARTED)

        # 5. 성공 응답 반환 - AI 응답 생성중
        response = chat_service.ResponseBuilder.build_response(
            req_msg.sid, req_msg.tid, codes.AppStatus.AI_PROCESSING_STARTED
        )
        ctx.log.debug(f"[WS]     << AI_PROCESSING_STARTED: sid={req_msg.sid}")
        return response

    except Exception as e:
        ctx.log.error(f"[WS]     - Processing error: sid={req_msg.sid}, error={e}")
        raise ValueError(f"Processing failed: sid={req_msg.sid}, error={e}")

# 핸들러 맵핑
MAP = {
    "ping": handle_ping,
    "chat-user": process_user_chat
}
