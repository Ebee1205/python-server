# utils/redis_utils.py
# 'redis_' prefix 가지도록 작성

from redis.exceptions import RedisError

def redis_set(ctx, key: str, value: str, ex: int = None):
    try:
        ctx.redis_handler.client.set(key, value, ex=ex)
        ctx.log.debug(f"Redis SET {key} = {value} (ex={ex})")
    except RedisError as e:
        ctx.redis_handler.log.error(f"Redis SET error: {str(e)}")

def redis_get(ctx, key: str) -> str | None:
    try:
        value = ctx.redis_handler.client.get(key)
        ctx.log.debug(f"Redis GET {key} = {value}")
        return value
    except RedisError as e:
        ctx.log.error(f"Redis GET error: {str(e)}")
        return None
