# utils/redis_utils.py

# 'redis_' pref
from redis.exceptions import RedisError

# 리스트에 값 삽입 (좌측 삽입)
async def redis_lpush(ctx, key: str, value: str):
    try:
        client = ctx.redis_handler.client
        await client.lpush(key, value)
        ctx.log.debug(f"[REDIS]    << LPUSH {key} = {value}")
    except Exception as e:
        ctx.log.error(f"[REDIS]    -- LPUSH error: {key}, {e}")