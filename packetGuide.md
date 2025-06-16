## ✅ Redis Stream 메시지 구조 (공통 표준)

모든 메시지는 아래와 같은 형태를 따르는 것이 가장 유지보수에 적합합니다:

```json
{
  "event": "이벤트명",          // 필수! 핸들러를 찾는 기준
  "tid": "타임스탬프 ID",       // 필수! 트래킹용 (ms 기준 추천)
  "userId": "user-1234",        // 필수! 사용자 식별
  "source": "web|ai|admin",     // 선택: 발신자 시스템 구분
  "message": "내용",            // 선택: 사람이 이해하기 쉬운 텍스트
  ... 기타 이벤트별 데이터 ...
}
```

---

## ✅ 필수 key 목록 및 설명

| Key       | 필수 여부      | 설명                                                              |
| --------- | ---------- | --------------------------------------------------------------- |
| `event`   | ✅ Yes      | 해당 메시지를 처리할 핸들러를 찾기 위한 식별자입니다. (`test-ping`, `sandbox-lint`, 등) |
| `tid`     | ✅ Yes      | 타임스탬프 기반 고유 ID (ms 단위로 생성하면 좋음). 트래킹 및 응답 식별에 사용됨               |
| `userId`  | ✅ Yes      | 요청자의 고유 ID. 로그 분석, 사용자 추적 등에 필수                                 |
| `source`  | ⭕ Optional | 메시지의 발신 주체 구분 (`web`, `ai`, `admin` 등). 선택적이지만 디버깅과 라우팅에 유용     |
| `message` | ⭕ Optional | 짧은 설명 메시지. 응답 구조에도 동일하게 포함 가능                                   |
| 기타        | ⭕ Optional | 이벤트별로 필요한 필드 (예: `prompt`, `model`, `lang`, `status`, 등)        |

---

## ✅ 예시: `test-ping` 요청 메시지

```json
{
  "event": "test-ping",
  "tid": "1750046502032",
  "userId": "sample-user",
  "source": "web",
  "message": "ping"
}
```

### 예시: `test-pong` 응답 메시지

```json
{
  "event": "test-pong",
  "tid": "1750046502032",
  "userId": "sample-user",
  "source": "ai",
  "message": "pong"
}
```

---

## ✅ 응답 저장을 위한 Redis Key 규칙 (추천)

| 용도    | Key 예시           | 설명                          |
| ----- | ---------------- | --------------------------- |
| 결과 저장 | `result:{tid}`   | API에서 `BLPOP`으로 대기하는 응답 저장소 |
| 상태 추적 | `status:{tid}`   | 처리 단계 상태 (optional)         |
| TTL   | 일반적으로 30초\~2분 설정 | 응답 안 오면 timeout 처리          |

---

## ✅ 기본 메시지 템플릿

```python
message = {
    "event": event_name,
    "tid": generate_tid(),         # str(int(time.time() * 1000))
    "userId": user_id,
    "source": "web",               # or "ai", "admin", ...
    "message": "optional text",
    **custom_fields                # prompt, input, status 등
}
```