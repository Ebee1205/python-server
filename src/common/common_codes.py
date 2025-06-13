class ResponseStatus:
    SUCCESS       = { "code": "S0000", "msg": "성공" }
    ERROR         = { "code": "E0000", "msg": "에러 발생" }
    BAD_REQUEST   = { "code": "E0001", "msg": "잘못된 요청입니다" }
    UNAUTHORIZED  = { "code": "E0002", "msg": "인증이 필요합니다" }
    FORBIDDEN     = { "code": "E0003", "msg": "접근이 거부되었습니다" }
    NOT_FOUND     = { "code": "E0004", "msg": "리소스를 찾을 수 없습니다" }
    CONFLICT      = { "code": "E0005", "msg": "이미 존재하는 리소스입니다" }
    SERVER_ERROR  = { "code": "E0500", "msg": "서버 내부 오류가 발생했습니다" }

    # 샌드박스 및 LLM 테스트용 추가 코드
    PROMPT_LINT_FAILED   = { "code": "E0400", "msg": "프롬프트 검사 결과 문제가 발견되었습니다" }
    LLM_MANAGER_MISSING  = { "code": "E0501", "msg": "LLM 매니저를 찾을 수 없습니다" }
    LLM_EXECUTION_FAILED = { "code": "E0502", "msg": "LLM 실행 중 오류가 발생했습니다" }
    SWEEP_PARAM_INVALID  = { "code": "E0401", "msg": "스위프 테스트 파라미터가 유효하지 않습니다" }


class AppStatus:
    USER_REGISTERED = "USER_REGISTERED"
    USER_LOGGED_IN  = "USER_LOGGED_IN"

    SESSION_CREATED = "SESSION_CREATED"
    SESSION_ENDED   = "SESSION_ENDED"

    USER_MESSAGE_RECEIVED = "USER_MESSAGE_RECEIVED"      

    AI_PROCESSING_STARTED = "AI_PROCESSING_STARTED"   
    AI_PROCESSING_FAILED  = "AI_PROCESSING_FAILED"      
    AI_MESSAGE_PROCESSED = "AI_MESSAGE_PROCESSED"      

    AI_MESSAGE_SENT       = "AI_MESSAGE_SENT"            