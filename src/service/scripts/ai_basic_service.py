# src/service/scripts/ai_basic_service.py

import orjson
from src.utils.redis_stream_utils import redis_stream_add

async def handle_test_ping(ctx, msg):
    
    pong_event = {
        "event": "test-pong",
        "tid": msg["tid"],
        "user_id": msg["user_id"],
        "message": "pong"
    }

    await redis_stream_add(ctx, ctx.cfg.redis_consumer.stream_key, pong_event)