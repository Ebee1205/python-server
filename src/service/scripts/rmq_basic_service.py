from datetime import datetime
import uuid

async def ping(ctx, msg):
    hd = msg.get("hd", {})
    tid = hd.get("tid") or f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"

    ctx.log.debug(f"📡 [RMQ] Ping requested | sid={hd.get('sid')} tid={tid}")

    return {
        "status": "pong",
        "message": msg,
        "tid": tid
    }
