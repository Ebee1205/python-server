# src/service/scripts/chat_service.py
import time
from uuid import uuid4
from dataclasses import dataclass
from typing import Optional, Dict, Any, Union

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
    tid: str
    sid: str
    mid: str
    msg: str
    type: Optional[str] = None
    role: Optional[str] = None
    user_id: Optional[str] = None
    
    @classmethod
    def from_req_msg(cls, msg: Dict[str, Any]) -> Optional['ChatMessage']:
        """웹소켓 메시지에서 ChatMessage 객체 생성"""
        try:
            hd = msg.get("hd", {})
            dt = msg.get("dt", {})
            
            return cls(
                tid=hd.get("tid"),
                sid=hd.get("sid"),
                mid=hd.get("mid"),
                msg=dt.get("msg"),
                type=hd.get("type"),
                role=hd.get("role"),
                user_id=hd.get("userId"),
            )
        except Exception:
            return None

def validate_message(message: ChatMessage) -> tuple[bool, str]:
    """Validate chat message by role and type."""
    
    if not message:
        return False, "Message parsing failed."

    valid_combinations = {
        MessageRole.USER: MessageType.CHAT_USER,
        MessageRole.SYSTEM: MessageType.CHAT_SYSTEM,
    }

    expected_type = valid_combinations.get(message.role)
    if expected_type is None:
        return False, f"Unsupported role: role={message.role}"

    if message.type != expected_type:
        return False, f"Invalid message type: role={message.role}, type={message.type} (expected: {expected_type})"

    if not all([message.sid, message.mid, message.msg]):
        return False, f"Missing required fields: sid={message.sid}, mid={message.mid}, msg={'present' if message.msg else 'missing'}"

    return True, ""

class SessionService:
    """세션 관리 서비스"""
    
    @staticmethod
    async def redis_stream_add_msg(ctx, message: ChatMessage, status: str) -> bool:
        """메시지를 redis 스트림에 추가"""
        stream_msg = {
            "tid": message.tid,
            "sid": message.sid,
            "mid": message.mid,
            "msg": message.msg or "",
            "type": message.type or MessageType.CHAT_USER,
            "role": message.role or MessageRole.USER,
            "userId": message.user_id or "system",
            "status": status,
        }
        return await redis_utils.redis_stream_add(ctx, "chat_stream", stream_msg)
    
    @staticmethod
    async def redis_update_session_state(ctx, message: Union[ChatMessage, Dict[str, Any]], status: str) -> bool:
        """세션 상태 업데이트 및 상태 백업"""
        now = int(time.time() * 1000)

        # sid 추출
        sid = message.sid if isinstance(message, ChatMessage) else message.get("sid")
        hash_key = f"chat:session:{sid}"

        # 시스템 상태값 추가
        await redis_utils.redis_hset_multi(ctx, hash_key, {
            "status": status,
            "uDate": now,
        })
        return await redis_utils.redis_hincrby(ctx, hash_key, "chatCount", 1)

class ResponseBuilder:
    """응답 메시지 생성 클래스"""
    
    @staticmethod
    def build_response(sid: str, status: str, message: str) -> Dict[str, Any]:
        """성공 응답 생성"""

        now = int(time.time() * 1000)
        return {
            "hd": {
                "tid": now,
                "sid": sid,
                "mid": id_generator.generate_mid(),
                "type": MessageType.CHAT_SYSTEM,
                "role": MessageRole.SYSTEM,
            },
            "dt": {
                "status": status,
                "message": message,
            },
            "codes": {
                **codes.ResponseStatus.SUCCESS,
            }
        }
    
    # TODO 에러 응답은 공통으로 빼던가 하자...
    @staticmethod
    def build_error_response(sid: str, status_code: Dict[str, Any]) -> Dict[str, Any]:
        """에러 응답 생성"""

        now = int(time.time() * 1000)
        return {
            "hd": {
                "tid": now,
                "sid": sid,
                "mid": id_generator.generate_mid(),
                "type": MessageType.ERROR,
                "role": MessageRole.SYSTEM,
            },
            "codes": {
                **status_code
            }
        }