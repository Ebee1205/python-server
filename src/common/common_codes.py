class ResponseStatus:
    SUCCESS       = { "code": "S0000", "message": "성공" }
    ERROR         = { "code": "E0000", "message": "에러 발생" }
    BAD_REQUEST   = { "code": "E0001", "message": "잘못된 요청입니다" }
    UNAUTHORIZED  = { "code": "E0002", "message": "인증이 필요합니다" }
    FORBIDDEN     = { "code": "E0003", "message": "접근이 거부되었습니다" }
    NOT_FOUND     = { "code": "E0004", "message": "리소스를 찾을 수 없습니다" }
    CONFLICT      = { "code": "E0005", "message": "이미 존재하는 리소스입니다" }
    SERVER_ERROR  = { "code": "E0500", "message": "서버 내부 오류가 발생했습니다" }