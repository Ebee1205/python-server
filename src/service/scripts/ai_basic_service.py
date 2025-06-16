# src/service/scripts/ai_basic_service.py

import orjson
from src.utils.rabbitmq_utils import rmq_send_response

async def handle_test_ping_rmq(ctx, msg: dict):
    tid = msg["hd"]["tid"]
    user_id = msg["hd"]["userId"]
    response_queue = "ankoko-from-algo"

    response = {
        "hd": {
            "event": "test-pong",
            "tid": tid,
            "userId": user_id
        },
        "dt": {
            "message": "pong"
        }
    }

    await rmq_send_response(ctx, response_queue, response)
