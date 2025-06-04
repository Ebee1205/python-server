fields = {
  "sid": sid,
  "userId": userId,
  "device": "web",
  "chatCount": 0,
  # "lastChatId": None, 
  # "lang": None,
  # "modelId": None,
  "cDate": tid,
  "uDate": tid,
  "lastAcc": tid,
  "status": "session_created",
  "ttl": 86400
}

response = {
  "code": "S00001",
  "msg": "Successed"
  "tid": tid,
  "sid": sid,
  "status": "session_created",
}


#-----------------#

result
{
  "type": "result",
  "sid": "s1234567890",
  "tid": "2025-05-23T12:10:02Z"
  "data": {
    "summary": "사용자는 날씨에 대해 질문함",
    "emotion": "neutral",
    "imgUrl": "/images/s1234567890.png",
    "title": "날씨 대화",
    "desc": "날씨 상태를 확인하는 유저와의 대화",
    "subj": "날씨",
    "tags": ["날씨", "정보"],
    "version": 1
  }
  "cDate": tid,
  "uDate": tid,
}

해쉬맵
{
  "sid": sid,
  "userId": userId,
  "device": "web",
  "chatCount": 0,
  "lastChatId": None, 
  "lang": None,
  "modelId": None,
  "status": "session_created",
  "cDate": tid,
  "uDate": tid,
  "lastAcc": tid,
  "ttl": 86400
}

#-----------------#

websocket 여기서는 hd/dt알아서 분리작성
user chat
{
  "hd": {
    "type": "chat-user",
    "role": "user",
    "sid": "s1234567890",
    "msgId": "m001",
    "userId": "u456425sdg4fhhjsdfg23445",
    "tid": "2025-05-23T12:00:05Z"
  },
  "dt": {
    "msg": "안녕",
    "metadata": {
      "lang": "ko"
    }
  }
}

ai chat
{
  "hd": {
    "type": "chat-ai",
    "role": "ai",
    "sid": "s1234567890",
    "msgId": "m002",
    "modelId": "gpt-4",
    "tid": "2025-05-23T12:00:06Z"
  },
  "dt": {
    "msg": "안녕하세요!",
    "metadata": {
      "tokens": 21,
      "emotion": "joy"
    }
  }
}

해쉬맵
{
  "sid": sid,
  "userId": userId,
  "device": "web",
  "chatCount": 0,
  "lastChatId": None, 
  "lang": None,
  "modelId": None,
  "status": "session_created",
  "cDate": tid,
  "uDate": tid,
  "lastAcc": tid,
  "ttl": 86400
}
---

@startuml
!define primary_key(x) <b>x</b>

entity User {
  primary_key(id): int
  userId: string             -- external user ID
  auth: string               -- guest, admin, user 등
  email: string              -- nullable
  password: string           -- nullable
  isDel: boolean
  cDate: datetime
  uDate: datetime
}

entity Session {
  primary_key(id): int
  sid: string                -- public session ID
  userId: string             -- User.userId
  lang: string           -- e.g., "ko", "en"
  device: string             -- "web", "mobile" 등
  status: string             -- active, ended, timeout
  lastAcc: datetime
  isDel: boolean
  cDate: datetime
  uDate: datetime
}

entity Result {
  primary_key(id): int
  rid: string                -- external result ID
  sid: string                -- Session.sid
  title: string
  desc: string
  subj: string
  tags: string               -- comma-separated or JSON
  version: int
  status: string             -- pending, confirmed
  imgUrl: string
  createdBy: string          -- userId
  isDel: boolean
  cDate: datetime
  uDate: datetime
}

entity Image {
  primary_key(id): int
  sid: string                -- session ID
  filePath: string
  type: string               -- MIME type
  size: int
  data: string               -- base64 or binary ref
  isDel: boolean
  cDate: datetime
  uDate: datetime
}

User ||--o{ Session : owns
Session ||--o{ Result : contains
@enduml