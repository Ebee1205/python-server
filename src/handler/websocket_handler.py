# handler/websocket_handler.py
from fastapi import WebSocket, WebSocketDisconnect
import json

class WebSocketHandler:
    def __init__(self, ctx):
        self.ctx = ctx
        self.log = ctx.log
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket, id: str = None):
        await websocket.accept()
        self.active_connections.append(websocket)
        if id:
            self.log.info(f"[WS]     - Connected: ID={id}, Client={websocket.client}")
        else:
            self.log.info(f"[WS]     - Connected: Client={websocket.client}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            self.log.info(f"[WS]     - Disconnected: Client={websocket.client}")

    async def receive_and_respond(self, websocket: WebSocket, processor):
        try:
            while True:
                str_msg = await websocket.receive_text()
                self.log.debug(f"[WS]     >> Received message: {str_msg}")
                msg = json.loads(str_msg)

                try:
                    response = await processor(self.ctx, websocket, msg)
                except Exception as e:
                    self.log.error(f"[WS]     - Router error: {str(e)}")
                    response = {
                        "status": "error",
                        "message": str(e)
                    }

                await websocket.send_json(response)
                self.log.debug(f"[WS]     << Sent response: {response}")

        except WebSocketDisconnect:
            self.disconnect(websocket)

        except Exception as e:
            self.log.error(f"[WS]     - Unexpected error: {str(e)}")
            await websocket.send_json({
                "status": "error",
                "errMsg": str(e)
            })
            self.disconnect(websocket)

    async def disconnect_all(self):
        self.log.info("[WS]     - Disconnecting all clients...")
        for websocket in list(self.active_connections):  # 복사본 사용
            try:
                await websocket.close()
            except Exception as e:
                self.log.warning(f"[WS]     - Failed to close client {websocket.client}: {e}")
            self.disconnect(websocket)  # 내부적으로 remove + log
