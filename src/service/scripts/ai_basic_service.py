# src/service/scripts/ai_basic_service.py

import orjson
from src.utils.redis_stream_utils import redis_stream_add

async def handle_test_ping(ctx, msg):
    ctx.log.info(f"[AI]    -- Received test-ping | tid={msg.get('tid')}")
    
    pong_event = {
        "event": "test-pong",
        "tid": msg["tid"],
        "userId": msg["userId"],
        "message": "pong"
    }

    await redis_stream_add(ctx, ctx.cfg.redis_consumer.stream_key, pong_event)
    ctx.log.info(f"[AI]    << Sent test-pong | tid={msg.get('tid')}")