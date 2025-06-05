# utils/websocket_utils.py
# 'ws_' prefix

import orjson
from src.utils import redis_utils

async def ws_send_response(ctx, sid: str, body: dict) -> bool:
    """
    WebSocket을 통해 클라이언트로 응답 메시지를 전송합니다.
    
    :param ctx: AppContext
    :param sid: str
    :param body: 보낼 메시지 (dict)
    :return: 성공 여부
    """
    log = ctx.log
    ws_handler = ctx.ws_handler

    ws = ws_handler.session_map.get(sid)
    if ws:
        try:
            await ws.send_json(body)
            log.info(f"[WS]     >> Send message to sid={sid}: {body}")
            return True
        except Exception as e:
            log.warning(f"[WS]     - Failed to send to sid={sid}: {e}")
            return False
    # else:
    #     log.warning(f"[WS]     - No active websocket for sid={sid}")
    #     return False
    
    # TODO 괜찮은 방법인지는 검증 필요할듯. 약간 strick한 방법처럼 느껴지기도하고...
    # WebSocket 연결이 없거나 전송 실패 시, Redis에 백업
    try:
        backup_key = f"chat:buffer:{sid}"
        await redis_utils.redis_lpush(ctx, backup_key, orjson.dumps(body))
        log.info(f"[WS]     !! No WS, backup message to Redis: {backup_key}")
        return True
    except Exception as e:
        log.error(f"[WS]     -- Redis backup failed: sid={sid}, error={e}")
        return False