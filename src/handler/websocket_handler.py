# websocket_handler.py

from fastapi import WebSocket, WebSocketDisconnect
import time

class WebSocketHandler:
    def __init__(self):
        self.active_connections = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"✅ 연결됨: {websocket.client}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print(f"🚫 연결 종료: {websocket.client}")

    async def receive_and_respond(self, websocket: WebSocket):
        try:
            while True:
                message = await websocket.receive_text()
                print(f"📨 받은 메시지: {message}")

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
