# websocket_handler.py

from fastapi import WebSocket, WebSocketDisconnect
import time
import json

class WebSocketHandler:
    def __init__(self, ctx):
        self.ctx = ctx
        self.log = ctx.log
        self.active_connections = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        sid = websocket.query_params.get("sid")

        if not sid:
            await websocket.close(code=4001)
            return

        # Redis에서 세션 존재 여부 확인
        # session_raw = self.ctx.redis.get(f"session:{sid}")
        # if not session_raw:
        #     await websocket.close(code=4002)
        #     return

        self.active_connections[sid] = websocket
        self.log.debug(f"[WS] Connected: {sid}")

    def disconnect(self, websocket: WebSocket):
        # sid → websocket 제거
        for sid, ws in list(self.active_connections.items()):
            if ws == websocket:
                del self.active_connections[sid]
                self.log.debug(f"[WS] Disconnected: {sid}")
                break

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

    async def send_to_sid(self, sid: str, data: dict):
        ws = self.active_connections.get(sid)
        if ws:
            await ws.send_json(data)

# TODO processor 패턴으로 변경됨, service 하위에 processor넣고... 근데 네이밍을 그냥 processor로 해도 될듯
