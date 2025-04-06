def ping(ctx):
    ctx.log.debug("📡 Ping requested in service layer")
    return {
        "status": "pong",
        "message": "Hello from basic_service"
    }
