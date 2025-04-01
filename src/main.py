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



ctx = app_context.AppContext()
ctx.load_config("src/service/conf/py-server-local.cfg.json")