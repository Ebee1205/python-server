
# service/scripts/basic_service.py

from datetime import datetime
import time, uuid, orjson

def ping(ctx):
    tid = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
    ctx.log.debug(f"📡 Ping requested in service layer | tid={tid}")

    return {
        "status": "pong",
        "message": "Hello from basic_service",
        "tid": tid
    }

import time, orjson
from src.utils.redis_stream_utils import redis_stream_add

async def handle_test_ping(ctx, user_id):
    tid = str(int(time.time() * 1000))
    ping_event = {
        "event": "test-ping",
        "tid": tid,
        "userId": user_id,
        "message": "ping"
    }

    await redis_stream_add(ctx, ctx.cfg.redis_consumer.stream_key, ping_event)
    ctx.log.info(f"[API]     >> Sent ping to Redis stream: {ctx.cfg.redis_consumer.stream_key}")

    # 결과 대기: 블로킹 pop으로 대기
    result_key = f"result:{tid}"
    try:
        value = await ctx.redis_handler.client.blpop(result_key, timeout=10)
        if value:
            _, data = value
            result = orjson.loads(data)
            return result
        else:
            return {"error": "timeout"}
    except Exception as e:
        ctx.log.error(f"[API]     !! Error waiting for pong result: {e}")
        return {"error": "exception", "details": str(e)}
    
async def handle_test_pong(ctx, msg):
    tid = msg.get("tid")
    if not tid:
        ctx.log.warning("[REDIS]    -- test-pong with no tid")
        return
    result_key = f"result:{tid}"
    await ctx.redis_handler.client.rpush(result_key, orjson.dumps(msg))
    await ctx.redis_handler.client.expire(result_key, 600)
    ctx.log.info(f"[WEB]    << Stored test-pong result for tid={tid}")