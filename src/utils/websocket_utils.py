# utils/websocket_utils.py
# 'ws_' prefix

import orjson
from src.service.scripts.chat_service import ChatMessage

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
    else:
        log.warning(f"[WS]     - No active websocket for sid={sid}")
        return False