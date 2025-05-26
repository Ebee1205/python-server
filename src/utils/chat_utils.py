# utils/chat_utils.py

# redis_utils.py의 유틸 함수를 이용해 채팅 관련한 state관리 등 작성 예시
# TODO 패킷 규격 설계 후 맞춰야할 듯.

from utils.redis_utils import (
    redis_stream_add,
    redis_stream_read,
    redis_stream_create_group
)

# 채팅 로그 저장
def save_chat_log(ctx, session_id: str, sender: str, message: str):
    stream_key = f"chat:session:{session_id}"
    log_data = {
        "sender": sender,
        "message": message
    }

    message_id = redis_stream_add(ctx, stream_key, log_data)
    if message_id:
        ctx.log.info(f"[{session_id}] 채팅 저장됨 → {message_id}")
    return message_id


# 채팅 히스토리 전체 조회
def get_chat_history(ctx, session_id: str):
    stream_key = f"chat:session:{session_id}"
    entries = redis_stream_read(ctx, stream_key, last_id="0")
    
    messages = []
    for stream in entries:
        for msg_id, data in stream[1]:
            messages.append({
                "id": msg_id,
                "sender": data.get("sender"),
                "message": data.get("message")
            })

    ctx.log.info(f"[{session_id}] 총 {len(messages)}개의 메시지 조회됨")
    return messages
