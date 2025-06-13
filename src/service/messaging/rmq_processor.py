# service/messaging/rmq_processor.py

from src.service.scripts.ws_basic_service import ws_ping
# 메시지 라우터
async def processor(ctx, msg, queue_name: str = "unknown"):
    hd = msg.get("hd", {})
    msg_type = hd.get('type')
    
    # 큐별 라우팅 맵 선택
    router = RMQ_PROCESSOR_MAP.get(queue_name)
    if not router:
        ctx.log.warning(f"[RMQ]     - No routing map for queue: {queue_name}")
        return {"status": "error", "msg": f"No routing for queue: {queue_name}"}

    handler = router.get(msg_type)
    if not handler:
        ctx.log.warning(f"[RMQ]     - Unknown msg type '{msg_type}' for queue '{queue_name}'")
        return {"status": "error", "msg": f"Unknown type: {msg_type}"}

    return await handler(ctx, msg)


RMQ_PROCESSOR_MAP = {
    "que-name": {
        "event-type": ws_ping
    },
    # "ankoko-from-algo": {
    #     "chat-user": chat.process_llm_request  
    # },
    # "ankoko-admin-from-algo": {
    #     "sandbox-lint": chat.process_llm_response,
    #     "sandbox-transform": chat.process_llm_response,
    #     "sandbox-sweep": chat.process_llm_response,
    #     "sandbox-single": chat.process_llm_response,
    #     "sandbox-batch": chat.process_llm_response,
    # },

}
