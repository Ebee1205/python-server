
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Body
from fastapi.middleware.cors import CORSMiddleware
from typing import Annotated
from uuid import uuid4
import time

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================
# 세션 생성 API
# =====================
@app.post("/api/session/connect")
async def connect_session(request: Request, userId: Annotated[str, Body(embed=True)]):
    tid = request.headers.get("tid") or str(int(time.time() * 1000))
    sid = f"s-{uuid4().hex[:10]}"
    now = int(time.time() * 1000)

    session = {
        "userId": userId,
        "sId": sid,
        "cDate": now,
        "state": "active"
    }

    print(f"[SESSION 생성] {session}")

    return {
        "hd": {
            "tid": int(tid),
            "type": "session"
        },
        "wvErr": "S0000",
        "wvMsg": "Success",
        "dt": session
    }

# =====================
# 세션 상태 조회 API
# =====================
@app.post("/api/session/state")
async def session_state(body: dict):
    session_id = body.get("sessionId")
    user_id = body.get("userId")
    now = int(time.time() * 1000)

    print(f"[SESSION 상태 요청] sessionId={session_id}, userId={user_id}")

    return {
        "hd": {
            "tid": now,
            "type": "session"
        },
        "wvErr": "S0000",
        "wvMsg": "Success",
        "dt": {
            "userId": user_id,
            "sId": session_id,
            "cDate": now - 10000,
            "state": "active"
        }
    }

# =====================
# WebSocket 연결 및 메시지 처리
# =====================
@app.websocket("/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()

    sid = websocket.query_params.get("sid")
    if not sid:
        await websocket.close(code=4001)
        return

    print(f"[WS 연결됨] sid={sid}")

    try:
        while True:
            msg = await websocket.receive_json()
            msg_type = msg.get("type")

            if msg_type == "ping":
                await websocket.send_json({
                    "status": "ok",
                    "type": "pong",
                    "tid": msg.get("tid")
                })

            elif msg_type == "chat":
                await process_chat_message(websocket, msg)

            else:
                await websocket.send_json({
                    "status": "error",
                    "message": f"Unknown type: {msg_type}"
                })
    except WebSocketDisconnect:
        print(f"[WS 연결 종료] sid={sid}")

# 채팅 메시지 처리
async def process_chat_message(websocket: WebSocket, message: dict):
    session_id = message.get("session_id")
    user_id = message.get("user_id")
    text = message.get("text")
    tid = message.get("tid") or str(int(time.time() * 1000))
    msg_id = str(int(time.time()))

    print(f"[CHAT 메시지 수신] {message}")

    await websocket.send_json({
        "status": "processing",
        "msg_id": msg_id,
        "session_id": session_id,
        "message": "🤖 AI 응답 생성 중..."
    })

    await websocket.send_json({
        "status": "S0000",
        "msg_id": msg_id,
        "tid": tid,
        "session_id": session_id,
        "user_id": user_id,
        "state": "processed_msg",
        "response": "✅ 테스트 응답입니다."
    })

# uvicorn main_test:app --reload --port 8000