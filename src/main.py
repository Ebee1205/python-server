# main.py

import app_context

# from fastapi import FastAPI, WebSocket
# from handler.websocket_handler import WebSocketHandler

# app = FastAPI()
# ws_handler = WebSocketHandler()

# @app.websocket("/ws/text")
# async def websocket_endpoint(websocket: WebSocket):
#     await ws_handler.connect(websocket)
#     await ws_handler.receive_and_respond(websocket)

def test_logging(logger):
    logger.info("-- FILE LOG TEST START --")
    logger.debug("   -test debug level")
    logger.info("    -test info level")
    logger.warning(" -test warn level")
    logger.error("   -test error level")
    logger.info("-- FILE LOG TEST END --")

ctx = app_context.AppContext()
ctx.load_config("src/service/conf/py-server-local.cfg.json")
ctx._init_logger()

test_logging(ctx.log)