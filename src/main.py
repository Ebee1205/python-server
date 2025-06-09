# main.py

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from src.app_context import AppContext
from src.routes.websocket_basic import router as basic_ws_router
from src.routes.basic_api import router as basic_router
from src.routes.session_api import router as session_router


app = FastAPI()
ctx = AppContext()
app.state.ctx = ctx

# CORS는 앱 생성 직후에만 등록 가능. 순서를 지킬 것
ctx.load_config("src/service/conf/py-server-local.cfg.json")

# TODO CORS 설정 위치 여기가 최선인가,,,
cors = ctx.cfg.http_config
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors.allow_origins,
    allow_credentials=cors.allow_credentials,
    allow_methods=cors.allow_methods,
    allow_headers=cors.allow_headers,
)
print(f"CORS 설정 완료: {cors.allow_origins}")

# TODO 라우터... 좀 무식하게 등록하는 중
app.include_router(basic_ws_router)
app.include_router(basic_router)
app.include_router(session_router)

# 이제야 on_startup 가능
@app.on_event("startup")
async def on_startup():
    try:
        # TODO 눈에 보여서 이렇게 작성하긴 했는데 보고 config() 혹은 init()으로 묶어서 작성하는것도 고려해보기
        print("     - Initializing application...")
        ctx = app.state.ctx

        # logger 초기화
        ctx._init_logger()
        test_logging(ctx.log)
        
        # 초기화
        ctx._init_websocket()
        ctx._init_redis()
        ctx._init_rmq()
        ctx._init_mqtt()

        await ctx.rmq_handler.connect()
        await ctx.rmq_handler.consume_multi()
        await ctx.redis_handler.connect()

        # mqtt connect 및 구독
        ctx.mqtt_handler.connect()
        for topic in ctx.cfg.mqtt.topics:
            ctx.mqtt_handler.subscribe(topic)

        ctx.log.info("     == Initialization complete")

    except Exception as e:
        ctx.log.error(f"     -- Initialization error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

@app.on_event("shutdown")
async def on_shutdown():
    ctx = app.state.ctx
    if ctx.log:
        ctx.log.info("     -- Shutting down application")

    # TODO app_context.py에 _destroy() 메서드로 추가 고려해보기
    # 역순으로 종료 (LIFO)
    if ctx.redis_handler:
        try:
            await ctx.redis_handler.disconnect()
            ctx.log.info("     -- Redis handler closed")
        except Exception as e:
            ctx.log.warning(f"     - Redis close failed: {e}")
    
    if ctx.ws_handler:
        try:
            await ctx.ws_handler.disconnect_all()
            ctx.log.info("     -- WebSocket handler closed")
        except Exception as e:
            ctx.log.warning(f"     - WebSocket close failed: {e}")

    if ctx.rmq_handler:
        try:
            await ctx.rmq_handler.disconnect()
            ctx.log.info("     -- RabbitMQ handler closed")
        except Exception as e:
            ctx.log.warning(f"     - RabbitMQ close failed: {e}")

    if ctx.mqtt_handler:
        try:
            await ctx.mqtt_handler.disconnect()
            ctx.log.info("     -- MQTT handler closed")
        except Exception as e:
            ctx.log.warning(f"     - MQTT close failed: {e}")
            
    # if ctx.db_handler:
    #     try:
    #         ctx.db_handler.close()
    #         ctx.log.info("DB handler closed")
    #     except Exception as e:
    #         ctx.log.warning(f"DB close failed: {e}")

def test_logging(logger):
    logger.info("-- FILE LOG TEST START --")
    logger.debug("   -test debug level")
    logger.info("    -test info level")
    logger.warning(" -test warn level")
    logger.error("   -test error level")
    logger.info("-- FILE LOG TEST END --")

    
# 실행코드
# uvicorn src.main:app --reload --port 8000