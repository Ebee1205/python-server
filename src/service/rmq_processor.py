# service/rmq_processor.py

from src.utils import rabbitmq_utils

# 메시지 라우터
async def processor(ctx, msg):
    msg_type = msg.get("type")
    handler = RMQ_PROCESSOR_MAP.get(msg_type)

    if not handler:
        ctx.log.warning(f"[RMQ] Unknown processor type: {msg_type}")
        return {"status": "error", "message": f"Unknown type: {msg_type}"}

    return await handler(ctx, msg)

# 핸들러 정의
async def handle_rmq_ping(ctx, msg):
    msg = {"status": "ok", "ankoko-to-algo": True, "data": "ping"}
    rabbitmq_utils.rmq_send_response(ctx, "ankoko-to-algo", msg), 
    return msg

async def handle_rmq_ping2(ctx, msg):
    return {"status": "ok", "ankoko-to-algo": True}


# 맵핑 테이블
RMQ_PROCESSOR_MAP = {
    "router_1": handle_rmq_ping,
    "router_2": handle_rmq_ping2,
}