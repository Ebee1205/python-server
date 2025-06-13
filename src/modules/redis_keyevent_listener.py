# src/modules/redis_keyevent_listener.py
import asyncio
from redis.asyncio import Redis

async def start_keyevent_listener(ctx):
    client: Redis = ctx.redis_handler.get_client()
    pubsub = client.pubsub()
    await pubsub.psubscribe("__keyevent@0__:*")

    ctx.log.info("[REDIS]    >> Keyevent listener started")

    async for message in pubsub.listen():
        if message["type"] == "pmessage":
            event = str(message["channel"])
            key = str(message["data"])

            ctx.log.info(f"[REDIS]    !! EVENT {event}: {key}")

            # 예: 자동 후처리 트리거
            if "expired" in event:
                await handle_expired_key(ctx, key)


async def handle_expired_key(ctx, key: str):
    ctx.log.debug(f"[REDIS]    .. Handling expired key: {key}")
    # 필요하면 여기서 후처리 로직 실행
