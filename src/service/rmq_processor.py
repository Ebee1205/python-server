# service/rmq_processor.py
from service.scripts.chat import chat_service
import src.common.common_codes as codes

from src.utils import redis_utils
from src.utils import rabbitmq_utils
from src.service.scripts import id_generator
from src.service.scripts.ai.llm_analze_service import llm_analyze_dialog

# TODO service name을 cfg 파일에서 부여하고 있기 때문에 이를 이용해서 라우터 섞이지 않게 방어로직 넣어주기(정확히는 시스템에 따라사용하는 맵 다르게)

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
        return {"status": "error", "msg": f"Unknown type: {msg_type}"}

    return await handler(ctx, msg)


# LLM 분석 처리 후 결과 발행 (from → to)
async def process_llm_request(ctx, msg):
    """LLM 분석 후 RMQ 발행 (ankoko-to-algo → ankoko-from-algo)"""

    req_msg = msg.get("dt", {})
    segments = [{"speaker": "user", "text": req_msg.get("msg", "")}]

    llm_result = await llm_analyze_dialog(ctx, segments)

    # 결과 메시지 구성
    result_msg = {
        "hd": {
            "tid": msg["hd"]["tid"],
            "sid": msg["hd"]["sid"],
            "mid": msg["hd"]["mid"],
            "type": "chat-system",
            "role": "system",
            "userId": msg["hd"].get("userId")
        },
        "dt": {
            "msg": req_msg.get("msg"),
            "llm_analysis": llm_result
        }
    }

    await rabbitmq_utils.rmq_send_response(ctx, "ankoko-from-algo", result_msg)
    return result_msg


# 2️⃣ LLM 결과를 WebSocket으로 전송 (from-algo → client)
async def process_llm_response(ctx, msg):
    """LLM 분석 결과 수신 → WebSocket 전달"""

    # 메시지 파싱
    req_msg = chat_service.ChatMessage.from_req_msg(msg)
    is_valid, err_msg = chat_service.validate_message(req_msg)
    if not is_valid:
        raise ValueError(f"Invalid message: sid={req_msg.sid}, reason={err_msg}")

    try:
        # Redis Stream 기록
        await chat_service.SessionService.redis_stream_add_msg(
            ctx, req_msg, codes.AppStatus.AI_MESSAGE_PROCESSED
        )

        # 세션 상태 업데이트
        await chat_service.SessionService.redis_update_session_state(
            ctx, req_msg, codes.AppStatus.AI_MESSAGE_SENT
        )

        # WebSocket 응답 구성
        result_msg = {
            "hd": msg["hd"],
            "dt": {
                "status": codes.AppStatus.AI_MESSAGE_SENT,
                "msg": msg["dt"].get("msg", ""),
                "llm_analysis": msg["dt"].get("llm_analysis", {})
            },
            "codes": {
                **codes.ResponseStatus.SUCCESS
            }
        }

        ws = ctx.ws_handler.session_map.get(req_msg.sid)
        if ws:
            try:
                await ws.send_json(result_msg)
            except Exception as e:
                return e
        else:
            # TODO: 유틸 함수로 분리 고려
            # ex) websocket_utils.backup_message_to_redis(ctx, sid, msg, ttl=3600)
            await redis_utils.redis_lpush(ctx, f"chat:buffer:{req_msg.sid}", result_msg)
            await redis_utils.redis_expire(ctx, f"chat:buffer:{req_msg.sid}", 3600)

        return result_msg

    except Exception as e:
        raise ValueError(f"Processing failed: sid={req_msg.sid}, error={e}")


# 메시지 라우팅
RMQ_PROCESSOR_MAP = {
    "chat-user": process_llm_request,   # 또는 적절한 핸들러로 교체
    "chat-system": process_llm_response
}
