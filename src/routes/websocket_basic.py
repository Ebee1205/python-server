# 웹소켓 기본 예제
# 웹소켓 핸들러를 사용하여 클라이언트와 서버 간의 메시지를 주고받는 예제임.
# routes/websocket_basic.py

from fastapi import APIRouter, WebSocket, Request

router = APIRouter()

@router.websocket("/ws")
async def websocket_basic(websocket: WebSocket, request: Request):
    ctx = request.app.state.ctx
    await ctx.ws_handler.connect(websocket)
    await ctx.ws_handler.receive_and_respond(websocket, mode="basic")
