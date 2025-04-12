# websocket_handler.py

from fastapi import WebSocket, WebSocketDisconnect
import time
import json

class WebSocketHandler:
    def __init__(self, ctx):
        self.ctx = ctx
        self.log = ctx.log
        self.active_connections = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.log.debug(f"Connected: {websocket.client}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            self.log.debug(f"Disconnected: {websocket.client}")

    async def receive_and_respond(self, websocket: WebSocket, mode="default", processor=None):
        try:
            while True:
                str_msg = await websocket.receive_text()
                self.log.debug(f"[{mode.upper()}] Received: {str_msg}")
                msg = json.loads(str_msg)

                # processor가 없으면 기본 처리
                if processor:
                    response = await processor(websocket, msg)
                else:
                    # TODO Header, Body 구분하여 작성하기
                    response = {
                        "status": "success",
                        "mode": mode,
                        "tid": int(time.time()),
                        "data": msg
                    }

                await websocket.send_json(response)
                self.log.debug(f"[{mode.upper()}] send response: {response}")

        except WebSocketDisconnect:
            self.disconnect(websocket)

        except Exception as e:
            await websocket.send_json({
                "status": "error",
                "message": str(e)
            })
            self.disconnect(websocket)
