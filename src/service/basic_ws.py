# 웹소켓 기본 예제
# 웹소켓 핸들러를 사용하여 클라이언트와 서버 간의 메시지를 주고받는 예제임.
# routes/basic_ws.py

from fastapi import APIRouter, WebSocket
from src.service.ws_processor import processor

router = APIRouter(prefix="/v1/basic", tags=["Basic"])

@router.websocket("/create")
async def websocket_chat(websocket: WebSocket):
    ctx = websocket.app.state.ctx

    # 쿼리 파라미터에서 id 추출
    id = websocket.query_params.get("id")
    if not id:
        await websocket.close(code=4001)
        return

    # id 전달하여 로그용 식별자 사용
    await ctx.ws_handler.connect(websocket, id=id)
    await ctx.ws_handler.receive_and_respond(websocket, processor=processor)