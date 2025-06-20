# service/scripts/health_service.py

import time
import orjson
import asyncio
from src.utils.redis_stream_utils import redis_stream_add

async def send_ping(ctx):
    """
    Send a minimal health-check event to Redis stream,
    then block until a matching health-ack is received.
    """
    tid = str(int(time.time() * 1000))

    # 1) health-check 전송 (API → Redis) >> 출력 송신
    await redis_stream_add(
        ctx,
        ctx.cfg.redis_consumer.stream_key,
        {"event": "health-check", "tid": tid}
    )
    ctx.log.info("API", f" >> Sent health-check | stream={ctx.cfg.redis_consumer.stream_key} | tid={tid}")

    result_key = f"result:{tid}"
    try:
        # 2) health-ack 대기 (Redis → API) << 입력 수신
        _, data = await ctx.redis_handler.client.blpop(result_key, timeout=10)
        ctx.log.debug("API", f" << Received health-ack | tid={tid}")
        return orjson.loads(data)

    except asyncio.TimeoutError:
        # 타임아웃 발생 시 WARNING
        ctx.log.warning("API", f" !! health-ack timeout | tid={tid}")
        return {"error": "timeout", "tid": tid}

    except Exception as e:
        # 그 외 예외 시 ERROR
        ctx.log.error("API", f" -- Waiting for health-ack failed: {e}")
        return {"error": "exception", "details": str(e)}


async def send_pong(ctx, msg):
    """
    Consume a health-check event from Redis stream,
    then push a minimal health-ack into the result list.
    """
    tid = msg.get("tid")
    if not tid:
        # tid 누락 시 WARNING
        ctx.log.warning("REDIS", " - Received health-check without tid")
        return

    ack = {"event": "health-ack", "tid": tid}
    result_key = f"result:{tid}"

    # 결과 리스트에 저장
    await ctx.redis_handler.client.rpush(result_key, orjson.dumps(ack))
    await ctx.redis_handler.client.expire(result_key, 600)
    ctx.log.info("REDIS", f" - Stored health-ack | tid={tid}")
