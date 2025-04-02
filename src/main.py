# main.py

from fastapi import FastAPI, WebSocket
from src.app_context import AppContext



def test_logging(logger):
    logger.info("-- FILE LOG TEST START --")
    logger.debug("   -test debug level")
    logger.info("    -test info level")
    logger.warning(" -test warn level")
    logger.error("   -test error level")
    logger.info("-- FILE LOG TEST END --")

ctx = AppContext()
ctx.load_config("src/service/conf/py-server-local.cfg.json")
ctx._init_logger()
test_logging(ctx.log)


ctx._init_websocket()

app = FastAPI()

@app.websocket("/ws/text")
async def websocket_endpoint(websocket: WebSocket):
    await ctx.ws_handler.connect(websocket)
    await ctx.ws_handler.receive_and_respond(websocket)

# 실행코드: uvicorn src.main:app --reload --port 8000