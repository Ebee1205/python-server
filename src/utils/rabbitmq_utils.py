# utils/rabbitmq_utils.py
# 'rmq_' prefix

import json
import aio_pika

async def rmq_send_response(ctx, queue_name: str, body: dict):
    """
    지정한 queue_name으로 직접 메시지를 전송합니다.
    default exchange 사용 (routing_key = queue_name).

    :param ctx: AppContext
    :param queue_name: 메시지를 보낼 큐 이름
    :param body: JSON 직렬화 가능한 dict
    """
    log = ctx.log
    rmq_handler = ctx.rmq_handler

    try:
        # 채널 보장
        if not rmq_handler.channel or rmq_handler.channel.is_closed:
            log.warning("[RMQ] Channel is closed. Reconnecting...")
            await rmq_handler.connect()

        message = aio_pika.Message(body=json.dumps(body).encode("utf-8"))

        channel = rmq_handler.get_channel()
        await channel.declare_queue(queue_name, durable=True)
        await channel.default_exchange.publish(message, routing_key=queue_name)

        log.debug(f"[RMQ]     - Sent respons '{queue_name}': {message}")

    except Exception as e:
        log.error(f"[RMQ] Failed to send response '{queue_name}': {e}")

# TODO rmq_send_error(ctx, queue_name, message, error_msg) 로 에러메시지 표준화