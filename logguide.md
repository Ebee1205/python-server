# 📘 Logging 규칙 가이드

서비스 운영 및 디버깅을 위한 통일된 로깅 스타일 가이드입니다.  
개발자 전원이 동일한 포맷으로 로그를 기록함으로써, 유지보수성과 가독성을 높입니다.

---

## ✅ 로그 기본 포맷

```
YYYY-MM-DD HH:mm:ss.SSS LEVEL [TAG] SYMBOL 메시지
```

- **LEVEL**: 로그 레벨 (INFO, DEBUG, WARNING, ERROR 등)
- **[TAG]**: 로그 발생 위치 또는 기능 태그
- **SYMBOL**: 동작 구분 기호 (입력/출력/처리/CRUD)
- **메시지**: 핵심 내용. 한 줄로 간결하게

---

## ✅ 심볼 정의

| 심볼  | 의미                  | 설명 예시                            |
|--------|-----------------------|----------------------------------------|
| `>>`   | 입력 수신 (Request)    | 외부/클라이언트에서 수신된 요청 데이터 |
| `<<`   | 출력 송신 (Response)  | 시스템에서 전송된 응답                 |
| `-`    | 내부 처리             | 주요 처리 과정, 상태 변화             |
| `++`   | 생성 (CREATE)         | Redis XADD, DB INSERT 등               |
| `==`   | 조회 (READ)           | Redis HGET, DB SELECT 등               |
| `!!`   | 갱신 (UPDATE)         | Redis HSET, DB UPDATE 등               |
| `--`   | 삭제 (DELETE)         | Redis DEL, DB DELETE 등               |

---

## ✅ TAG 네이밍 규칙

- 기능 또는 위치 기반으로 작성
- 복잡하게 세분화하지 않고 **단일 모듈명**으로 작성

| 태그 예시   | 설명                         |
|-------------|------------------------------|
| `[APP]`      | 애플리케이션 초기화, 종료     |
| `[WS]`       | 웹소켓 통신 처리             |
| `[API]`      | API 핸들러                   |
| `[REDIS]`    | Redis 작업 전반               |
| `[DB]`       | 데이터베이스 쿼리 관련        |
| `[AUTH]`     | 인증/인가 처리               |

---

## ✅ 예시 로그

```text
2025-05-22 12:00:00.123 INFO  [APP]     - Application initialized
2025-05-22 12:00:01.456 DEBUG [WS]      >> Received message from client: {...}
2025-05-22 12:00:01.457 DEBUG [REDIS]  ++ XADD chat_stream 17478... {session_id=..., ...}
2025-05-22 12:00:01.458 DEBUG [REDIS]  !! HSET chat:session:s-xxx state=waiting_ai result=1
2025-05-22 12:00:01.459 DEBUG [WS]      << Sent response: {...}
2025-05-22 12:00:03.000 INFO  [APP]     - Cleaning up resources
```

---

## ❌ 금지사항

- ❌ 이모지, 유니코드, 특수문자 사용 금지 (→, ✓ 등)
- ❌ 강제 공백으로 정렬 맞추기 (예: `[INFO ]` 대신 `INFO`)
- ❌ JSON 전체 로그 한 줄에 너무 길게 쓰기 → 요약 또는 간략화
- ❌ print()로 직접 찍지 말고 로깅 함수 또는 포맷에 맞춰 작성

---

## 🧩 팁

- 필요한 경우 로그 마지막에 `tid`, `session_id`, `user_id` 등 주요 식별자 포함
- DB/Redis 작업은 반드시 결과 값도 함께 남기기