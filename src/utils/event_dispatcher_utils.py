# src/utils/event_dispatcher_utils.py

import importlib

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
