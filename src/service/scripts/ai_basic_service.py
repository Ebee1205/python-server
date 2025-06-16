# src/service/scripts/ai_basic_service.py

import orjson
from src.utils.redis_stream_utils import redis_stream_add

async def handle_test_ping_rmq(ctx, msg: dict):
    tid = msg["tid"]
    user_id = msg["userId"]
    stream_key = "ankoko:result:stream"

    response = {
        "event": "test-pong",
        "tid": tid,
        "userId": user_id,
        "message": "pong"
    }

    await redis_stream_add(ctx, stream_key, response)
    ctx.log.info(f"[REDIS]    >> Sent pong response to stream: {stream_key}")
