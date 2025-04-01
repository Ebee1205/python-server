from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import whisper
import tempfile
from pydub import AudioSegment
import wave
import time

app = FastAPI()
model = whisper.load_model("base")

# CORS 설정 (모든 도메인 허용, 필요시 변경 가능)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/stt/test")
async def test_http_response():
    return JSONResponse(content={
        "status": "success",
        "message": "이것은 테스트 응답입니다.",
        "text": "안녕하세요. 이것은 Whisper STT 서버의 테스트 메시지입니다."
    })

# 1. 조각 업로드 방식
@app.post("/api/stt/upload-audio")
async def transcribe_audio(audio: UploadFile = File(...)):
    try:
        print('upload-audio')
        start_time = time.time()

        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_input:
            temp_input.write(await audio.read())
            temp_input_path = temp_input.name

        # webm -> wav 변환
        sound = AudioSegment.from_file(temp_input_path)
        temp_wav_path = temp_input_path.replace(".webm", ".wav")
        sound.export(temp_wav_path, format="wav")

        # Whisper STT 처리
        result = model.transcribe(temp_wav_path)
        end_time = time.time()

        return JSONResponse(content={
            "status": "success",
            "start_time": start_time,
            "end_time": end_time,
            "duration": round(end_time - start_time, 3),
            "text": result["text"]
        })

    except Exception as e:
        return JSONResponse(status_code=500, content={
            "status": "error",
            "message": str(e)
        })

# 2. 실시간 스트리밍 방식
@app.websocket("/ws/stt")
async def websocket_stt(websocket: WebSocket):
    await websocket.accept()
    print("🎧 WebSocket 연결됨")

    audio_buffer = b''
    recording_start = None

    try:
        while True:
            try:
                chunk = await websocket.receive_bytes()

                if recording_start is None:
                    recording_start = time.time()

                audio_buffer += chunk

                # 3초 기준 데이터량 이상이면 처리
                if len(audio_buffer) >= 16000 * 2 * 3:
                    recording_end = time.time()

                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmpfile:
                        wf = wave.open(tmpfile.name, 'wb')
                        wf.setnchannels(1)
                        wf.setsampwidth(2)  # 16-bit PCM
                        wf.setframerate(16000)
                        wf.writeframes(audio_buffer)
                        wf.close()

                        try:
                            result = model.transcribe(tmpfile.name)
                            response = {
                                "status": "success",
                                "start_time": recording_start,
                                "end_time": recording_end,
                                "duration": round(recording_end - recording_start, 3),
                                "text": result["text"]
                            }
                        except Exception as e:
                            response = {
                                "status": "error",
                                "message": f"STT 처리 중 오류 발생: {str(e)}",
                                "start_time": recording_start,
                                "end_time": recording_end,
                                "duration": round(recording_end - recording_start, 3)
                            }

                        await websocket.send_json(response)

                        # 초기화
                        audio_buffer = b''
                        recording_start = None

            except WebSocketDisconnect:
                print("❌ 클라이언트 연결 끊김")
                break

    except Exception as e:
        print("❌ WebSocket 서버 오류:", str(e))
        await websocket.send_json({
            "status": "error",
            "message": f"WebSocket 내부 오류: {str(e)}"
        })
        await websocket.close()


# ✅ 텍스트 입력용 WebSocket 엔드포인트
@app.websocket("/ws/text")
async def websocket_text(websocket: WebSocket):
    await websocket.accept()
    print("💬 WebSocket 연결됨 (/ws/text)")

    try:
        while True:
            try:
                message = await websocket.receive()

                if "text" in message:
                    text_input = message["text"]
                    print(f"📨 수신된 텍스트: {text_input}")

                    start_time = time.time()

                    # Whisper 처리 시뮬레이션 (실제 Whisper는 오디오 입력 기반이지만 여기선 에코)
                    result_text = f"✅ 처리 완료: '{text_input}'"

                    end_time = time.time()

                    await websocket.send_json({
                        "status": "success",
                        "start_time": start_time,
                        "end_time": end_time,
                        "duration": round(end_time - start_time, 3),
                        "text": result_text
                    })

            except WebSocketDisconnect:
                print("❌ 클라이언트 연결 끊김")
                break

    except Exception as e:
        print("❌ WebSocket 서버 오류:", str(e))
        await websocket.send_json({
            "status": "error",
            "message": f"WebSocket 내부 오류: {str(e)}"
        })
        await websocket.close()