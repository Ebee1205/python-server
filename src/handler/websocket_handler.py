# websocket_handler.py

from fastapi import WebSocket, WebSocketDisconnect
import time

class WebSocketHandler:
    def __init__(self, ctx):
        self.log = ctx.log
        self.active_connections = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.log.debug("WebSocket connected")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            self.log.debug("WebSocket disconnected")

    async def receive_and_respond(self, websocket: WebSocket):
        try:
            while True:
                message = await websocket.receive_text()

                self.log.debug(f"Received: {message}")
                start_time = time.time()
                response = {
                    "status": "success",
                    "text": f"✅ 처리 완료: '{message}'",
                    "timestamp": start_time
                }
                await websocket.send_json(response)

        except WebSocketDisconnect:
            self.disconnect(websocket)

        except Exception as e:
            await websocket.send_json({
                "status": "error",
                "message": str(e)
            })
            self.disconnect(websocket)
