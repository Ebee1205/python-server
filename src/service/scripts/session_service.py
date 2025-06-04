# src/service/scripts/id_generator.py
import time
from uuid import uuid4
from dataclasses import dataclass
from typing import Optional, Dict, Any

from src.service.scripts import id_generator
import src.common.common_codes as codes
from src.utils import redis_utils

class MessageRole:
    """메시지 역할 정의"""
    USER = "user"
    SYSTEM = "system"

class MessageType:
    """메시지 타입 정의"""
    CHAT_USER = "chat-user"
    CHAT_SYSTEM = "chat-system"
    ERROR = "error"

@dataclass
class ChatMessage:
    """채팅 메시지 데이터 클래스"""
    role: str
    msg_type: str
    sid: str
    user_id: str
    mid: str
    tid: str
    text: str
    
    @classmethod
    def from_websocket_msg(cls, msg: Dict[str, Any]) -> Optional['ChatMessage']:
        """웹소켓 메시지에서 ChatMessage 객체 생성"""
        try:
            hd = msg.get("hd", {})
            dt = msg.get("dt", {})
            
            return cls(
                role=hd.get("role"),
                msg_type=hd.get("type"),
                sid=hd.get("sid"),
                user_id=hd.get("userId"),
                mid=hd.get("mid"),
                tid=hd.get("tid"),
                text=dt.get("msg")
            )
        except Exception:
            return None

def validate_message(chat_msg: ChatMessage) -> tuple[bool, str]:
    """Validate chat message by role and type."""
    
    if not chat_msg:
        return False, "Message parsing failed."

    valid_combinations = {
        MessageRole.USER: MessageType.CHAT_USER,
        MessageRole.SYSTEM: MessageType.CHAT_SYSTEM,
    }

    expected_type = valid_combinations.get(chat_msg.role)
    if expected_type is None:
        return False, f"Unsupported role: role={chat_msg.role}"

    if chat_msg.msg_type != expected_type:
        return False, f"Invalid message type: role={chat_msg.role}, type={chat_msg.msg_type} (expected: {expected_type})"

    if not all([chat_msg.sid, chat_msg.user_id, chat_msg.text]):
        return False, f"Missing required fields: sid={chat_msg.sid}, userId={chat_msg.user_id}, text={'present' if chat_msg.text else 'missing'}"

    return True, ""

class SessionService:
    """세션 관리 서비스"""
    
    @staticmethod
    async def add_user_message(ctx, chat_msg: ChatMessage) -> bool:
        """사용자 메시지를 스트림에 추가"""
        stream_msg = {
            "tid": chat_msg.tid,
            "sid": chat_msg.sid,
            "userId": chat_msg.user_id,
            "text": chat_msg.text,
            "type": MessageType.CHAT_USER,
            "role": MessageRole.USER,
            "mid": id_generator.generate_mid(),
            "status": codes.AppStatus.USER_MESSAGE_RECEIVED,
        }
        return await redis_utils.redis_stream_add(ctx, "chat_stream", stream_msg)
    
    @staticmethod
    async def update_session_state(ctx, sid: str, tid: str, status: str) -> bool:
        """세션 상태 업데이트"""
        now = int(time.time() * 1000)
        hash_key = f"chat:session:{sid}"
        
        await redis_utils.redis_hset_multi(ctx, hash_key, {
            "state": status,
            "uDate": now,
        })
        
        return await redis_utils.redis_hincrby(ctx, hash_key, "chatCount", 1)
    

class ResponseBuilder:
    """응답 메시지 생성 클래스"""
    
    @staticmethod
    def build_response(sid: str, tid: str, status: str, message: str) -> Dict[str, Any]:
        """성공 응답 생성"""

        now = int(time.time() * 1000)
        return {
            "hd": {
                "type": MessageType.CHAT_SYSTEM,
                "role": MessageRole.SYSTEM,
                "tid": now,
                "sid": sid,
                "mid": id_generator.generate_mid(),
            },
            "dt": {
                "status": status,
                "message": message,
            },
            "codes": {
                **codes.ResponseStatus.SUCCESS,
            }
        }
    
    @staticmethod
    def build_error_response(sid: str, tid: str, status_code: Dict[str, Any]) -> Dict[str, Any]:
        """에러 응답 생성"""
        return {
            "hd": {
                "type": MessageType.ERROR,
                "role": MessageRole.SYSTEM,
                "tid": tid,
                "sid": sid,
                "mid": id_generator.generate_mid(),
            },
            "codes": {
                **status_code
            }
        }