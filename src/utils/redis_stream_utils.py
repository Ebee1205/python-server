# utils/redis_utils.py

# 'redis_' pref
from redis.exceptions import RedisError
import orjson
import asyncio

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
    

async def redis_stream_wait_result(ctx, stream_key: str, timeout=10_000):
    """
    Redis Stream에서 지정된 키의 결과를 블로킹으로 대기하여 반환합니다.

    :param ctx: AppContext (redis_handler 필요)
    :param stream_key: stream 이름 (예: sandbox_result:<task_id>)
    :param timeout: 블로킹 시간 (ms)
    :return: 메시지 dict or None
    """
    log = ctx.log
    redis = ctx.redis_handler.get_client()

    try:
        entries = await redis.xread({stream_key: "0"}, block=timeout, count=1)

        if entries:
            _, messages = entries[0]
            message_id, data = messages[0]

            # 값이 JSON 문자열인 경우 파싱 시도
            parsed_data = {
                k: orjson.loads(v) if isinstance(v, str) and v.startswith("{") else v
                for k, v in data.items()
            }

            log.info(f"[REDIS]    << Result received from '{stream_key}': {parsed_data}")
            return parsed_data

        log.warning(f"[REDIS]    == No result in '{stream_key}' (timeout={timeout}ms)")
        return None

    except Exception as e:
        log.error(f"[REDIS]    -- Error reading stream '{stream_key}': {e}")
        return None

async def redis_stream_find_result(ctx, stream_key: str, task_id: str, timeout: int = 10_000) -> dict | None:
    """
    Redis 스트림에서 task_id에 해당하는 결과 메시지를 블로킹 없이 조회합니다.
    (polling 방식)

    :param ctx: AppContext
    :param stream_key: 예: 'sandbox_result_stream'
    :param task_id: 찾을 작업 ID
    :param timeout: 최대 대기 시간 (ms)
    :return: 메시지 dict or None
    """
    log = ctx.log
    redis = ctx.redis_handler.get_client()
    deadline = asyncio.get_event_loop().time() + (timeout / 1000)

    last_id = "0-0"

    while asyncio.get_event_loop().time() < deadline:
        try:
            entries = await redis.xrange(stream_key, min=last_id, max="+", count=10)

            for msg_id, data in entries:
                if data.get("task_id") == task_id:
                    parsed = {
                        k: orjson.loads(v) if isinstance(v, str) and v.startswith("{") else v
                        for k, v in data.items()
                    }
                    log.info(f"[REDIS]    << Result found for task_id={task_id}: {parsed}")
                    return parsed

                last_id = msg_id  # 다음 조회를 위해 업데이트

            await asyncio.sleep(0.5)  # 너무 자주 조회하지 않도록

        except Exception as e:
            log.error(f"[REDIS]    !! Error polling result stream: {e}")
            return None

    log.warning(f"[REDIS]    == No result for task_id={task_id} after timeout")
    return None
