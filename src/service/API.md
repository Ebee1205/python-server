# TryAngle API Specification

본 문서는 **TryAngle** 서비스의 백엔드 API 엔드포인트 및 통신 규격을 정의합니다.

---

## 공통 응답 패킷 규격 (Standard Response Format)

모든 API 응답은 일관된 분석과 트래킹을 위해 아래의 공통 구조를 엄격히 준수해야 합니다.

### 📋 패킷 구조 제약 사항
- Root Structure: 모든 응답은 `tid`, `status`, `data` 세 가지 최상위 필드를 포함해야 합니다.
- Transaction ID (`tid`): API 호출 시점의 Unix Timestamp (ms 단위, BigInt)를 할당하여 요청의 고유성을 식별합니다.
- Status Object: 내부 상태 코드와 메시지를 포함합니다.
    - `code`: 서비스 내부 상태 코드 (성공: `S0000`, 오류: `E` 계열 코드)
    - `msg`: 사용자/개발자 친화적 상태 메시지
- Data Object: 비즈니스 로직 결과가 들어가는 영역입니다. 조회 결과가 없을 경우 `null` 대신 빈 객체(`{}`) 또는 빈 배열(`[]`)을 반환하는 것을 권장합니다.

### 📄 응답 예시 (JSON)
```json
{
    "tid": 1705298638704,
    "status": {
        "code": "S0000",
        "msg": "성공"
    },
    "data": {
        "dorm": 3,
        "selectTag": [
            "디자인학부",
            "이른 기상",
            "과제",
            "비흡연"
        ],
        "notes": "이갈이, 냄새, 소등 양해 필요"
    }
}
```

### 코드 관리
응답의 `status.code` 값은 프로젝트의 공통 코드 정의 파일을 참조하도록 합니다: `src/common/common_codes.py`.

---

## 📋 설계 가이드라인
* **ID Mapping:** 모든 식별자(`id`)는 보안 및 일관성을 위해 URL Path가 아닌 **Request Body**에 JSON 형태로 포함하여 전달합니다.
* **Timestamp:** 모든 시간 데이터(`cDate`, `uDate`)는 **Unix Timestamp (BigInt)** 형식을 사용합니다.
* **Architecture:** * 메타데이터는 **RDBMS**(`tb_` 시리즈)에서 관리합니다.
    * 비정형 AI 분석 결과는 **MongoDB**(`aiDocId`)를 통해 조회합니다.
    * 실제 파일 리소스는 **Cloudflare R2** 스토리지에 저장됩니다.

---

## 1. 시스템 공통 (Common)
| 기능 | 엔드포인트 | 설명 |
| :--- | :--- | :--- |
| 헬스체크 | `/ping` | 서버 및 네트워크 상태 확인 |

---

## 2. 사용자 및 인증 (Auth/User)
| 기능 | 엔드포인트 | 설명 |
| :--- | :--- | :--- |
| 아이디 중복 확인 | `/api/auth/exists` | 사용자 ID 존재 여부 체크 |
| 이메일 확인 | `/api/auth/checkEmail` | 가입 이메일 유효성 및 중복 체크 |
| 사용자 생성 | `/api/auth/signup` | 회원가입 (`tb_user` 생성) |
| 사용자 토큰 | `/api/auth/token` | Access/Refresh Token 갱신 |
| 로그인 | `/api/auth/login` | 세션 시작 및 인증 토큰 발급 |
| 로그아웃 | `/api/auth/logout` | 세션 종료 및 토큰 무효화 |
| 내 정보 조회 | `/api/me` | 현재 로그인한 사용자의 프로필 정보 반환 |
| 내 정보 수정 | `/api/auth/update` | 사용자 정보(별명, 연락처 등) 업데이트 |

---

## 3. 태그 관리 (Tag)
| 기능 | 엔드포인트 | 설명 |
| :--- | :--- | :--- |
| 태그 목록 | `/api/tag/list` | 전체 태그 리스트 및 필터 검색 |
| 태그 생성 | `/api/tag/create` | 신규 태그 코드 및 명칭 등록 |
| 태그 조회 | `/api/tag/get` | 특정 태그의 상세 정보 및 부모 태그 확인 |
| 태그 수정 | `/api/tag/update` | 태그 정보 변경 |
| 태그 삭제 | `/api/tag/delete` | 태그 정보 삭제 |

---

## 4. 시스템 로그 (System/Log)
| 기능 | 엔드포인트 | 설명 |
| :--- | :--- | :--- |
| 로그 목록 | `/api/system/list` | 시스템 활동 로그 목록 조회 |
| 로그 생성 (테스트) | `/api/system/log` | 서버 사이드 관리용 로그 등록 |
| 로그 생성 (디바이스) | `/api/system/send` | 온디바이스 AI 연산 및 클라이언트 로그 전송 |
| 로그 상세 조회 | `/api/system/get` | 특정 로그의 상세 페이로드 확인 |

---

## 5. 파일 관리 (Files/R2)
| 기능 | 엔드포인트 | 설명 |
| :--- | :--- | :--- |
| 파일 등록 | `/api/files/create` | Cloudflare R2 스토리지 파일 업로드 |
| 파일 목록 | `/api/files/list` | 업로드된 파일 메타데이터 목록 조회 |
| 파일 정보 확인 | `/api/files/get` | Request Body의 `fileId` 기준 파일 메타데이터 조회 |
| 파일 다운로드 URL | `/api/files/getPresigned` | Request Body의 `fileId` 기준 Presigned URL 반환 |
| 파일 삭제 | `/api/files/delete` | Request Body의 `fileId` 기준 스토리지 파일 삭제 |

---

## 6. 이미지 카테고리 (Image Category)
| 기능 | 엔드포인트 | 설명 |
| :--- | :--- | :--- |
| 이미지 카테고리 목록 | `/api/ctg/list` | 이미지 카테고리 전체 목록 조회 |
| 이미지 카테고리 등록 | `/api/ctg/create` | 이미지 카테고리 등록 |
| 이미지 카테고리 조회 | `/api/ctg/get` | 이미지 카테고리 조회 |
| 이미지 카테고리 수정 | `/api/ctg/update` | 이미지 카테고리 수정 |
| 이미지 카테고리 삭제 | `/api/ctg/delete` | 이미지 카테고리 삭제 |

---

## 7. 이미지 참조 데이터 (Ref/Image)
| 기능 | 엔드포인트 | 설명 |
| :--- | :--- | :--- |
| 이미지 목록 | `/api/ref/list` | 이미지 메타데이터 목록 및 카테고리별 필터링 |
| 이미지 등록 | `/api/ref/create` | 신규 이미지 메타데이터 및 AI 데이터 ID 등록 |
| 이미지 조회 | `/api/ref/get` | 이미지 상세 정보 및 MongoDB AI 데이터 병합 조회 |
| 이미지 수정 | `/api/ref/update` | 이미지 가중치, 제목, 설명 등 정보 수정 |
| 이미지 삭제 | `/api/ref/delete` | 이미지 레코드 및 연관 관계 삭제 |

---

## 8. 북마크 관리 (Bookmark)
| 기능 | 엔드포인트 | 설명 |
| :--- | :--- | :--- |
| 레퍼런스 북마크 토글 | `/api/bmk/toggle` | 특정 레퍼런스의 북마크 상태를 추가 또는 해제 |
| 북마크 목록 조회 | `/api/bmk/list` | 사용자가 북마크한 레퍼런스 목록 조회 |

---

## 9. 상품 관리 (Product)
| 기능 | 엔드포인트 | 설명 |
| :--- | :--- | :--- |
| 상품 목록 | `/api/prod/list` | 등록된 상품 목록 조회 |
| 상품 등록 (Admin) | `/api/prod/create` | 관리자 권한으로 신규 상품 등록 |
| 상품 수정 (Admin) | `/api/prod/update` | 관리자 권한으로 상품 정보 수정 |
| 상품 삭제 (Admin) | `/api/prod/delete` | 관리자 권한으로 상품 정보 삭제 |

---

## 10. 아카이브 관리 (Snap/Archive)
| 기능 | 엔드포인트 | 설명 |
| :--- | :--- | :--- |
| 스냅 사진 목록 | `/api/snap/list` | 스냅 사진 아카이브 목록 조회 |
| 스냅 사진 조회 | `/api/snap/get` | 특정 스냅 사진 상세 정보 조회 |
| 스냅 사진 등록 | `/api/snap/create` | 신규 스냅 사진 아카이브 등록 |
| 스냅 사진 수정 (Admin) | `/api/snap/update` | 관리자 권한으로 스냅 사진 정보 수정 |
| 스냅 사진 삭제 (Admin) | `/api/snap/delete` | 관리자 권한으로 스냅 사진 삭제 |

---

## 11. 세션 관리 (Session)
| 기능 | 엔드포인트 | 설명 |
| :--- | :--- | :--- |
| 세션 시작 | `/api/session/start` | 사용자 세션 시작 및 상태 생성 |
| 세션 종료 | `/api/session/end` | 진행 중인 사용자 세션 종료 |
| 세션 토큰 | `/api/session/token` | 세션 유지 또는 재인증용 토큰 발급 및 갱신 |
| 세션 상태 변경 | `/api/session/status` | 세션의 현재 상태값 변경 |

---