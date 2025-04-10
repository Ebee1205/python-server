# utils/redis_utils.py
# 'redis_' pref
from redis.exceptions import RedisError


# 단일 키의 값을 조회
# - key: 조회할 Redis 키
# - return: 문자열 값 또는 None
def redis_get(ctx, key):
    try:
        client = ctx.redis_handler.client
        value = client.get(key)
        ctx.log.debug(f"GET key: {key} → {value}")
        return value
    except RedisError as e:
        ctx.log.error(f"redis_get error - key: {key}, error: {str(e)}")
        return None


# 단일 키-값을 저장
# - expire_sec: 초 단위 만료 시간 (None이면 무제한)
# - return: 성공 시 True, 실패 시 False
def redis_set(ctx, key, value, expire_sec=None):
    try:
        client = ctx.redis_handler.client
        success = client.set(key, value, ex=expire_sec)
        if not success:
            ctx.log.warning(f"SET command failed - key: {key}")
        ctx.log.debug(f"SET key: {key}, value: {value}, expire: {expire_sec}")
        return success
    except RedisError as e:
        ctx.log.error(f"redis_set error - key: {key}, error: {str(e)}")
        return False


# 기존 키가 있을 경우에만 값 갱신
# - return: 갱신 성공 시 True, 키 없으면 False
def redis_update(ctx, key, new_value):
    try:
        client = ctx.redis_handler.client
        if client.exists(key) > 0:
            client.set(key, new_value)
            ctx.log.debug(f"UPDATE key: {key}, new_value: {new_value}")
            return True
        else:
            ctx.log.warning(f"Key not found for update: {key}")
            return False
    except RedisError as e:
        ctx.log.error(f"redis_update error - key: {key}, error: {str(e)}")
        return False


# 주어진 prefix로 시작하는 키 검색, 값 함께 반환
# - return: {key: value} 형태의 딕셔너리
def redis_search_by_prefix(ctx, prefix):
    try:
        client = ctx.redis_handler.client
        pattern = f"{prefix}*"
        keys = client.keys(pattern)
        results = {k: client.get(k) for k in keys}
        ctx.log.debug(f"SEARCH prefix: {prefix}, found: {len(results)} keys")
        return results
    except RedisError as e:
        ctx.log.error(f"redis_search_by_prefix error - prefix: {prefix}, error: {str(e)}")
        return {}


# 주어진 키 삭제
# - return: 삭제된 키가 있으면 True, 없으면 False
def redis_delete(ctx, key):
    try:
        client = ctx.redis_handler.client
        result = client.delete(key)
        ctx.log.debug(f"DELETE key: {key}, deleted: {result}")
        return result > 0
    except RedisError as e:
        ctx.log.error(f"redis_delete error - key: {key}, error: {str(e)}")
        return False


# 키의 존재 여부 확인
# - return: 존재하면 True, 없으면 False
def redis_exists(ctx, key):
    try:
        client = ctx.redis_handler.client
        result = client.exists(key) > 0
        ctx.log.debug(f"EXISTS key: {key} → {result}")
        return result
    except RedisError as e:
        ctx.log.error(f"redis_exists error - key: {key}, error: {str(e)}")
        return False


# 키에 TTL(만료 시간) 설정
# - ttl: 초 단위 만료 시간
# - return: 설정 성공 시 True
def redis_expire(ctx, key, ttl):
    try:
        client = ctx.redis_handler.client
        result = client.expire(key, ttl)
        ctx.log.debug(f"EXPIRE key: {key}, ttl: {ttl} → result: {result}")
        return result
    except RedisError as e:
        ctx.log.error(f"redis_expire error - key: {key}, error: {str(e)}")
        return False


# 해시 구조의 필드에 값 설정
# - return: 새 필드이면 1, 기존 필드 덮어쓰기이면 0
def redis_hset(ctx, key, field, value):
    try:
        client = ctx.redis_handler.client
        result = client.hset(key, field, value)
        ctx.log.debug(f"HSET key: {key}, field: {field}, value: {value}")
        return result
    except RedisError as e:
        ctx.log.error(f"redis_hset error - key: {key}, field: {field}, error: {str(e)}")
        return False


# 해시 구조에서 필드의 값 조회
# - return: 값 또는 None
def redis_hget(ctx, key, field):
    try:
        client = ctx.redis_handler.client
        value = client.hget(key, field)
        ctx.log.debug(f"HGET key: {key}, field: {field} → {value}")
        return value
    except RedisError as e:
        ctx.log.error(f"redis_hget error - key: {key}, field: {field}, error: {str(e)}")
        return None


# Redis Stream에 메시지 추가
def redis_stream_add(ctx, stream_key, message: dict):
    try:
        client = ctx.redis_handler.client
        message_id = client.xadd(stream_key, message)
        ctx.log.debug(f"XADD stream: {stream_key}, id: {message_id}, message: {message}")
        return message_id
    except RedisError as e:
        ctx.log.error(f"redis_stream_add error - stream: {stream_key}, error: {str(e)}")
        return None


# Redis Stream에서 메시지 읽기
def redis_stream_read(ctx, stream_key, last_id="$", block_ms=0):
    try:
        client = ctx.redis_handler.client
        response = client.xread({stream_key: last_id}, block=block_ms)
        ctx.log.debug(f"XREAD stream: {stream_key}, last_id: {last_id} → response: {response}")
        return response
    except RedisError as e:
        ctx.log.error(f"redis_stream_read error - stream: {stream_key}, error: {str(e)}")
        return []


# Consumer Group에서 메시지 읽기
def redis_stream_group_read(ctx, group, consumer, stream_key, count=1):
    try:
        client = ctx.redis_handler.client
        response = client.xreadgroup(group, consumer, {stream_key: ">"}, count=count)
        ctx.log.debug(f"XREADGROUP group: {group}, consumer: {consumer}, stream: {stream_key} → {response}")
        return response
    except RedisError as e:
        ctx.log.error(f"redis_stream_group_read error - group: {group}, error: {str(e)}")
        return []


# 메시지 ACK
def redis_stream_ack(ctx, stream_key, group, message_id):
    try:
        client = ctx.redis_handler.client
        result = client.xack(stream_key, group, message_id)
        ctx.log.debug(f"XACK stream: {stream_key}, group: {group}, id: {message_id} → {result}")
        return result
    except RedisError as e:
        ctx.log.error(f"redis_stream_ack error - stream: {stream_key}, id: {message_id}, error: {str(e)}")
        return False


# Consumer Group 생성
def redis_stream_create_group(ctx, stream_key, group_name):
    try:
        client = ctx.redis_handler.client
        client.xgroup_create(stream_key, group_name, id="0", mkstream=True)
        ctx.log.debug(f"XGROUP CREATE stream: {stream_key}, group: {group_name}")
        return True
    except RedisError as e:
        if "BUSYGROUP" in str(e):
            ctx.log.debug(f"Group already exists: {group_name} on stream: {stream_key}")
            return True
        ctx.log.error(f"redis_stream_create_group error - stream: {stream_key}, error: {str(e)}")
        return False