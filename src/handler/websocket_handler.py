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
        self.log.debug(f"Connected: {websocket.client}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            self.log.debug(f"Disconnected: {websocket.client}")

    async def receive_and_respond(self, websocket: WebSocket, mode="default", processor=None):
        try:
            while True:
                message = await websocket.receive_text()
                self.log.debug(f"[{mode.upper()}] Received: {message}")

                timestamp = int(time.time())

                # processor가 없으면 기본 처리
                if processor:
                    response = await processor(message, mode, timestamp)
                else:
                    # TODO Header, Body 구분하여 작성하기
                    response = {
                        "status": "success",
                        "mode": mode,
                        "tid": timestamp,
                        "data": message
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
