# TryAngle 데이터베이스 설계 명세서 (v1.3.0)

본 문서는 000 서비스의 RDBMS(PostgreSQL/MySQL 등) 스키마를 정의합니다. 
이미지 분석 결과와 시스템 로그 일부는 noneSQL DB 및 Cloudflare R2에 분산 저장되며, 본 DB는 사용자, 태그, 000와 이들 간의 관계를 관리합니다.

## 1. 공통 설정

* **Timestamp:** 모든 일시 컬럼은 Unix Timestamp(`bigint`)를 사용합니다.
* **Character Set:** `utf8mb4`
* **Naming Convention:**
    * 기본 테이블: `tb_{name}`
    * 매핑 테이블: `mtb_{name}`
    * 생성일/수정일: `cDate` / `uDate`
* **Role Enum:** `SUPER_ADMIN`, `ADMIN`, `CLIENT`
* **Primary Key Strategy:** 기본 PK 전략은 `BIGINT AUTO_INCREMENT`입니다. 단, `tb_session.id`는 외부 로그 매핑 키로 사용되므로 예외적으로 src.core.id_generator.generate_sid로 수동 할당 PK를 사용합니다.
* **Status Code Convention:** 상태값은 문자열 enum 대신 정수 코드(`int`)를 사용합니다.

---

## 2. 테이블 정의

### 2.1 사용자 정보 (`tb_user`)
사용자의 계정 정보, 프로필, 권한과 활성 상태를 관리합니다.

| 컬럼명 | 타입 | 제약사항 | 설명 |
| :--- | :--- | :--- | :--- |
| **id** | bigint | PK, Auto Increment | 사용자 고유 식별자 |
| **email** | varchar | Unique, Not Null | 로그인 이메일 |
| **password** | varchar | - | 암호화된 비밀번호 |
| **name** | varchar | - | 실명 |
| **nickname** | varchar | - | 서비스 내 별명 |
| **phone** | varchar | - | 연락처 |
| **emailConf** | varchar | Default: "2" | 이메일 인증 여부 (`1`: 인증, `2`: 미인증) |
| **desc** | text | - | 프로필 자기소개 |
| **fileId** | varchar | - | 프로필 이미지 경로 |
| **role** | enum(user_role) | Default: "CLIENT" | 권한 (`SUPER_ADMIN`, `ADMIN`, `CLIENT`) |
| **state** | int | Default: 1 | 계정 상태 (`0: INACTIVE`, `1: ACTIVE`) |
| **extra** | json | - | 기타 부가 정보 |
| **cDate** | bigint | - | 생성일 (Unix Timestamp) |
| **uDate** | bigint | - | 수정일 (Unix Timestamp) |


## 3. 관계 요약


---

## 4. 특이사항 및 구현 가이드

1. **noneSQL DB 연동:** `tb_img.aiDocId`는 레퍼런스 이미지 분석/가이드 문서와 연결되고, `tb_session.id`는 시스템 로그 컬렉션과 매핑됩니다.
2. **저장소 분리:** 원본 및 결과 이미지 파일은 Cloudflare R2에 저장하고, RDBMS에는 경로와 메타데이터만 저장하는 구성을 전제로 합니다.
3. **계정 상태 관리:** `tb_user.state`로 계정 활성/비활성 여부를 관리하며, 물리 삭제 정책은 별도로 운영합니다.
4. **상태값 관리:** `tb_user.state`, `tb_session.sStat`, `tb_prod.pStat`, `tb_snap.gender`는 정수 코드 기반으로 관리합니다.
5. **데이터 무결성:** `tb_user`, `tb_img`, `tb_prod`, `tb_session` 삭제 시 `mtb_bookmark`, `mtb_img_tag`, `tb_snap`에 대한 Cascade 또는 비활성화 정책을 별도로 결정해야 합니다.
6. **성능 최적화:** `tb_user.state`, `tb_img`의 `useCnt`, `expWeight`, `pri`, `tb_prod`의 `pStat`, `tb_snap`의 `viewCnt`, `tb_session`의 `sStat`, `sDate`는 조회 패턴에 따라 보조 인덱스 검토가 필요합니다.
7. **전환 주의사항:** 현재 애플리케이션 API/서비스 레이어는 일부 문자열 ID 생성 로직과 기존 상태값 표현을 사용 중일 수 있으므로, 스키마 변경과 함께 서비스 레이어 호환성을 점검해야 합니다.


## 5. Cloudflare R2 폴더 구조 정의서 (tryangle-images)
| 폴더명 | 용도 | DB 매핑 필드 | 파일명 예시 (Example) |
| :--- | :--- | :--- | :--- |
