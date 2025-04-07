# main.py

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from src.app_context import AppContext
from src.routes.websocket_basic import router as basic_ws_router
from src.routes.basic_api import router as basic_router


app = FastAPI()
ctx = AppContext()
app.state.ctx = ctx
# ✨ CORS는 앱 생성 직후에만 등록 가능!
ctx.load_config("src/service/conf/py-server-local.cfg.json")  # 최소한 http_config가 있어야 함
cors = ctx.cfg.http_config

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors.allow_origins,
    allow_credentials=cors.allow_credentials,
    allow_methods=cors.allow_methods,
    allow_headers=cors.allow_headers,
)

# TODO websocket_router.py 등으로 분리
app.include_router(basic_ws_router)

# http://localhost:8000/docs
# GET /api/basic/ping
app.include_router(basic_router)

# 👉 이제야 on_startup 가능
@app.on_event("startup")
async def on_startup():
    try:
        # 눈에 보여서 이렇게 작성하긴 했는데 보고 config() 혹은 init()으로 묶어서 작성하는것도 고려해보기
        ctx = app.state.ctx

        # logger 초기화
        ctx._init_logger()
        test_logging(ctx.log)

        # TODO 구조상 안된다고 하더이다... 확인필요
        # cors 적용
        # ctx.setup_cors(app)   

        # websocket 초기화
        ctx._init_websocket()

        ctx.log.info("App initialization complete")

    except Exception as e:
        print("🚨 초기화 중 오류 발생:", str(e))
        import traceback
        traceback.print_exc()
        raise

@app.on_event("shutdown")
async def on_shutdown():
    ctx = app.state.ctx
    if ctx.log:
        ctx.log.info("Cleaning up resources...")

    # TODO app_context.py에 _destroy() 메서드로 추가
    # if ctx.db_handler:
    #     try:
    #         ctx.db_handler.close()
    #         ctx.log.info("DB handler closed")
    #     except Exception as e:
    #         ctx.log.warning(f"DB close failed: {e}")

    # if ctx.redis_handler:
    #     try:
    #         ctx.redis_handler.close()
    #         ctx.log.info("Redis handler closed")
    #     except Exception as e:
    #         ctx.log.warning(f"Redis close failed: {e}")

    # if ctx.rmq_handler:
    #     try:
    #         ctx.rmq_handler.disconnect()
    #         ctx.log.info("RMQ handler disconnected")
    #     except Exception as e:
    #         ctx.log.warning(f"RMQ disconnect failed: {e}")

def test_logging(logger):
    logger.info("-- FILE LOG TEST START --")
    logger.debug("   -test debug level")
    logger.info("    -test info level")
    logger.warning(" -test warn level")
    logger.error("   -test error level")
    logger.info("-- FILE LOG TEST END --")

    
# 실행코드
# uvicorn src.main:app --reload --port 8000