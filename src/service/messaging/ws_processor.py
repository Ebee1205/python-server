import src.common.common_codes as codes

from src.service.scripts.ws_basic_service import handle_ping

async def processor(ctx, websocket, msg):
    hd = msg.get("hd")
    msg_type = hd.get('type')
    tid = hd.get("tid")
    sid = hd.get("sid")
    mid = hd.get("mid")

    handler = MAP.get(msg_type)
    if not handler:
        ctx.log.warning(f"[WS]     - Unknown message type: {msg_type}, tid={tid}, sid={sid}, mid={mid}")
        return {"status": "error", "message": f"Unknown type: {msg_type}"}

    return await handler(ctx, websocket, msg)

# 핸들러 맵핑
MAP = {
    "ping": handle_ping,
}
