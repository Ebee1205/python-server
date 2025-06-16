
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

async def handle_test_ping(ctx, user_id: str):
    tid = str(int(time.time() * 1000))
    stream_key = "ankoko:task:stream"
    redis_result_key = f"result:{tid}"

    message = {
        "event": "test-ping",
        "tid": tid,
        "userId": user_id,
        "message": "ping"
    }

    await redis_stream_add(ctx, stream_key, message)
    ctx.log.info(f"[API]     >> Sent ping to Redis stream: {stream_key}")

    # 응답 대기 TTL 설정
    await ctx.redis_handler.client.expire(redis_result_key, 30)

    try:
        result_data = await ctx.redis_handler.client.blpop(redis_result_key, timeout=10)

        if result_data:
            pong = orjson.loads(result_data[1])
            return {
                "status": "SUCCESS",
                "tid": tid,
                "pong_response": pong
            }

        return {
            "status": "SUCCESS",
            "tid": tid,
            "pong_response": {"status": "timeout", "message": "AI 응답 없음"}
        }

    except Exception as e:
        ctx.log.error(f"[API]     >> Error waiting for pong: {e}")
        return {
            "status": "SUCCESS",
            "tid": tid,
            "pong_response": {"status": "error", "message": str(e)}
        }
    
async def handle_test_pong_result(ctx, msg: dict):
    """
    test-pong 결과를 Redis에 저장 (BLPOP으로 API 응답 대기용)
    """
    try:
        tid = msg.get("tid")
        if not tid:
            ctx.log.warning("[REDIS]    !! No TID in test-pong message")
            return

        result_key = f"result:{tid}"
        result_json = orjson.dumps(msg)

        await ctx.redis_handler.client.lpush(result_key, result_json)
        await ctx.redis_handler.client.expire(result_key, 30)

        ctx.log.info(f"[REDIS]    >> Pong result stored to Redis: {result_key}")
    except Exception as e:
        ctx.log.error(f"[REDIS]    -- Failed to process test-pong result: {e}")
