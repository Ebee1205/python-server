# src/utils/event_dispatcher_utils.py

import importlib
import orjson 

def load_handler(handler_path: str):
    module_path, name = handler_path.rsplit(".", 1)
    mod = importlib.import_module(module_path)
    return getattr(mod, name)


async def dispatch_event(ctx, event, source_type, queue_name=None, **kwargs):
    project = ctx.cfg.project_name
    mapping = ctx.event_map.get(project, {}).get(source_type, {}).get(event)

    if not mapping:
        ctx.log.warning(f"[{source_type.upper()}] - No handler for event '{event}'")
        return {"status": "error", "msg": f"No handler for event: {event}"}

    if queue_name and mapping.get("queue") != queue_name:
        ctx.log.warning(f"[{source_type.upper()}] - Mismatched queue '{queue_name}' for event '{event}'")
        return {"status": "error", "msg": f"Queue mismatch"}

    handler_path = mapping["handler"]
    handler = load_handler(handler_path)

    if list(kwargs.keys()) == ["msg"]:
        return await handler(ctx, kwargs["msg"])
    elif list(kwargs.keys()) == ["websocket", "msg"]:
        return await handler(ctx, kwargs["websocket"], kwargs["msg"])
    else:
        return await handler(ctx, **kwargs)

# Redis 키 이벤트 전용 dispatcher
async def dispatch_redis_event(ctx, event: str, key: str, fields: dict) -> dict:
    try:
        ctx.log.info(f"[DISPATCH]  << Processing Redis event '{event}' for key={key}")
        
        # 기존 이벤트 매핑 구조를 활용하여 디스패치
        result = await dispatch_event(
            ctx, 
            event=event, 
            source_type="redis_keyevent",
            fields=fields,
            key=key
        )
        
        ctx.log.info(f"[DISPATCH]  !! Event '{event}' processing result: {result}")
        
        # 결과를 result 키에 푸시 (API가 대기 중)
        tid = fields.get("tid")
        if tid and result.get("status") != "error":
            result_key = f"result:{tid}"
            result_json = orjson.dumps(result)
            
            # lpush로 결과 전송 (blpop에서 받음)
            await ctx.redis_handler.client.lpush(result_key, result_json)
            ctx.log.info(f"[DISPATCH]  >> Result pushed to {result_key}")
        elif not tid:
            ctx.log.warning(f"[DISPATCH]  -- No tid found in fields, cannot send result")
        
        return result
        
    except Exception as e:
        ctx.log.error(f"[DISPATCH]  -- Error dispatching Redis event '{event}': {e}")
        error_result = {"status": "error", "message": str(e), "event": event}
        
        # 에러도 결과로 전송
        tid = fields.get("tid")
        if tid:
            result_key = f"result:{tid}"
            result_json = orjson.dumps(error_result)
            await ctx.redis_handler.client.lpush(result_key, result_json)
            
        return error_result