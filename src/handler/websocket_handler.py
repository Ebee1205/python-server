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
        self.log.debug(f"[WS] Connected: {websocket.client}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            self.log.debug(f"[WS] Disconnected: {websocket.client}")

    async def receive_and_respond(self, websocket: WebSocket, processor):
        try:
            while True:
                str_msg = await websocket.receive_text()
                self.log.debug(f"[WS] Received: {str_msg}")
                msg = json.loads(str_msg)

                try:
                    response = await processor(self.ctx, websocket, msg)
                except Exception as e:
                    self.log.error(f"[WS] Router Error: {str(e)}")
                    response = {
                        "status": "error",
                        "message": str(e)
                    }

                await websocket.send_json(response)
                self.log.debug(f"[WS] Sent response: {response}")

        except WebSocketDisconnect:
            self.disconnect(websocket)

        except Exception as e:
            await websocket.send_json({
                "status": "error",
                "message": str(e)
            })
            self.disconnect(websocket)


# TODO processor 패턴으로 변경됨, service 하위에 processor넣고... 근데 네이밍을 그냥 processor로 해도 될듯
