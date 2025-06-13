# utils/redis_utils.py

# 'redis_' pref
from redis.exceptions import RedisError

# Redis Stream에 메시지 추가
async def redis_stream_add(ctx, stream_key, message: dict):
    try:
        client = ctx.redis_handler.client
        message_id = await client.xadd(stream_key, message)
        ctx.log.debug(f"[REDIS]    ++ XADD {stream_key} > {message_id}, {message}")
        return message_id
    except RedisError as e:
        ctx.log.error(f"[REDIS]    -- XADD error: {stream_key}, {str(e)}")
        return None

# Redis Stream에서 메시지 읽기
async def redis_stream_read(ctx, stream_key, last_id="$", block_ms=0):
    try:
        client = ctx.redis_handler.client
        response = await client.xread({stream_key: last_id}, block=block_ms)
        ctx.log.debug(f"[REDIS]    == XREAD {stream_key} from {last_id} > {response}")
        return response
    except RedisError as e:
        ctx.log.error(f"[REDIS]    -- XREAD error: {stream_key}, {str(e)}")
        return []


# Consumer Group에서 메시지 읽기
async def redis_stream_group_read(ctx, group, consumer, stream_key, count=1):
    try:
        client = ctx.redis_handler.client
        response = await client.xreadgroup(group, consumer, {stream_key: ">"}, count=count)
        ctx.log.debug(f"[REDIS]    == XREADGROUP {group}/{consumer} > {response}")
        return response
    except RedisError as e:
        ctx.log.error(f"[REDIS]    -- XREADGROUP error: {group}, {str(e)}")
        return []


# 메시지 ACK
async def redis_stream_ack(ctx, stream_key, group, message_id):
    try:
        client = ctx.redis_handler.client
        result = await client.xack(stream_key, group, message_id)
        ctx.log.debug(f"[REDIS]    !! XACK {stream_key}/{group} > {message_id} > {result}")
        return result
    except RedisError as e:
        ctx.log.error(f"[REDIS]    -- XACK error: {stream_key}, {message_id}, {str(e)}")
        return False

# Consumer Group 생성
async def redis_stream_create_group(ctx, stream_key, group_name):
    try:
        client = ctx.redis_handler.client
        await client.xgroup_create(stream_key, group_name, id="0", mkstream=True)
        ctx.log.debug(f"[REDIS]    ++ XGROUP.CREATE {stream_key} > {group_name}")
        return True
    except RedisError as e:
        if "BUSYGROUP" in str(e):
            ctx.log.debug(f"[REDIS]    - XGROUP already exists: {group_name} on {stream_key}")
            return True
        ctx.log.error(f"[REDIS]    -- XGROUP.CREATE error: {stream_key}, {str(e)}")
        return False