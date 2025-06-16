
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

from src.utils.rabbitmq_utils import rmq_send_response

async def handle_test_ping(ctx, user_id: str):
    tid = str(int(time.time() * 1000))
    request_queue = "ankoko-to-algo"
    response_queue = "ankoko-from-algo"
    redis_result_key = f"result:{tid}"

    message = {
        "hd": {
            "event": "test-ping",
            "tid": tid,
            "userId": user_id
        },
        "dt": {
            "message": "ping"
        }
    }


    await rmq_send_response(ctx, request_queue, message)
    ctx.log.info(f"[API]     >> Sent ping to {request_queue}")

    # 응답 Redis 키 생성 후 대기
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
    test-pong 이벤트에 대한 결과 메시지를 처리하고 Redis에 저장합니다.
    Redis Key: result:{tid}
    """
    try:
        hd = msg.get("hd", {})
        dt = msg.get("dt", {})

        tid = hd.get("tid")
        if not tid:
            ctx.log.warning("[RMQ]     !! No TID in pong message")
            return

        result_key = f"result:{tid}"
        result_json = orjson.dumps(dt)

        # 추후 Redis TTL만 걸고 대기하는 구조가 아닌 WebSocket 등의 Push로 응답 처리하는 방식으로 변경 시 삭제 가능
        # test-pong 수신 후
        await ctx.redis_handler.client.lpush(result_key, result_json)
        await ctx.redis_handler.client.expire(result_key, 30)  # 여기서 TTL 설정

        ctx.log.info(f"[RMQ]     >> Pong result stored to Redis: {result_key}")

    except Exception as e:
        ctx.log.error(f"[RMQ]     -- Failed to process test-pong: {e}")
