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

    # dispatch_event 내부

    if not mapping:
        ctx.log.warning(f"[{source_type.upper()}] - No handler for event '{event}'")
        return {"status": "error", "msg": f"No handler for event: {event}"}

    if queue_name and mapping.get("queue") and mapping["queue"] != queue_name:
        ctx.log.warning(f"[{source_type.upper()}] - Mismatched queue '{queue_name}' for event '{event}'")
        return {"status": "error", "msg": "Queue mismatch"}

    handler_path = mapping["handler"]
    handler = load_handler(handler_path)

    if list(kwargs.keys()) == ["msg"]:
        return await handler(ctx, kwargs["msg"])
    elif list(kwargs.keys()) == ["websocket", "msg"]:
        return await handler(ctx, kwargs["websocket"], kwargs["msg"])
    else:
        return await handler(ctx, **kwargs)


async def dispatch_redis_event(ctx, event: str, key: str, fields: dict) -> dict:
    try:
        ctx.log.info(f"[DISPATCH]  << Processing Redis event '{event}' for key={key}")

        result = await dispatch_event(
            ctx,
            event=event,
            source_type="redis_keyevent",
            fields=fields,
            key=key
        )

        ctx.log.info(f"[DISPATCH]  !! Event '{event}' processing result: {result}")

        tid = fields.get("tid")
        if tid and result.get("status") != "error":
            result_key = f"result:{tid}"
            result_json = orjson.dumps(result)
            await ctx.redis_handler.client.lpush(result_key, result_json)
            ctx.log.info(f"[DISPATCH]  >> Result pushed to {result_key}")
        elif not tid:
            ctx.log.warning("[DISPATCH]  -- No tid found in fields, cannot send result")

        return result

    except Exception as e:
        ctx.log.error(f"[DISPATCH]  -- Error dispatching Redis event '{event}': {e}")
        error_result = {"status": "error", "message": str(e), "event": event}

        tid = fields.get("tid")
        if tid:
            result_key = f"result:{tid}"
            result_json = orjson.dumps(error_result)
            await ctx.redis_handler.client.lpush(result_key, result_json)

        return error_result
