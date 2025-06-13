async def handle_ping(ctx, websocket, msg):
    sid = msg.get("hd", {}).get("sid")
    ctx.log.debug(f"[WS]     >> Ping request received: sid={sid}")
    return {"status": "ok", "type": "pong", "tid": msg.get("tid")}