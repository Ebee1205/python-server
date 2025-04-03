# routes/websocket_basic.py

from fastapi import APIRouter, WebSocket, Request

router = APIRouter()

@router.websocket("/ws")
async def websocket_basic(websocket: WebSocket, request: Request):
    ctx = request.app.state.ctx
    await ctx.ws_handler.connect(websocket)
    await ctx.ws_handler.receive_and_respond(websocket, mode="basic")
