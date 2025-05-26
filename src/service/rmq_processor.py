# service/rmq_processor.py

from src.utils import redis_utils

# 메시지 라우터
async def processor(ctx, msg):
    processor_name = msg.get("type")
    handler = RMQ_PROCESSOR_MAP.get(processor_name)

    if not handler:
        ctx.log.warning(f"[RMQ] Unknown processor type: {processor_name}")
        return {"status": "error", "message": f"Unknown type: {processor_name}"}

    return await handler(ctx, msg)

# 핸들러 정의
async def handle_rmq_ping(ctx, msg):
    return {"status": "ok", "rmq": True}


# 맵핑 테이블
RMQ_PROCESSOR_MAP = {
    "router_1": handle_rmq_ping,
    "router_2": handle_rmq_ping,
}