---
trigger: always_on
description: SQL Labs 프로젝트 작업 시 항상 참고하는 규칙
---

# QueryCraft 프로젝트 작업 규칙

## 0. 기본 규칙
- 구현 계획과 설명은 항상 한글로 할 것
- docs/TODO_LIST.md는 언제 어디서든 했던 것들 중 더 이상 작업을 하지 않고 퇴근하거나 자러갈때 다음에 이어서 할 일을 적어놓는 곳으로 모든 작업이 끝나고 dev 브랜치에 push 해놓고 한 일들은 TODO_LIST에서 삭제한다.

## 1. 코드 변경 후 배포

**개발 서버 dev 브랜치**
- 개발서버는 워크스테이션에 배포되어있음
- **백엔드**: `docker compose restart backend`
- **프론트엔드**: `docker compose build frontend && docker compose up -d frontend`
- 환경변수 변경 시 반드시 컨테이너 재시작 필요

**상용 서버 main 브랜치**
- 상용 서버는 GCP에 배포되어있음
- 상용 브랜치는 push하면 자동 배포 Github Actions 있음

## 2. 코드 스타일

### Python
- 타입 힌트 필수, Docstring 작성
- 로깅: `common.logging.get_logger(__name__)` 사용

### TypeScript
- 함수형 컴포넌트 + Hooks 사용
- 분석 이벤트: `analytics` 서비스 통해 트래킹 (직접 mixpanel 호출 금지)

## 3. API 구조

| Prefix | 용도 |
|--------|------|
| `/auth/*` | 인증 (로그인/회원가입) |
| `/problems/*` | 문제 조회 |
| `/sql/*` | SQL 실행/제출 |
| `/admin/*` | 관리자 전용 |
| `/stats/*` | 통계/리더보드 |

## 4. 데이터베이스

- **PostgreSQL**: 사용자, 제출 기록, 문제 메타데이터
- **DuckDB**: Stream 분석용 대용량 이벤트
- **파일**: `problems/daily/` (일별 문제 JSON)

## 5. 문제 생성 및 채점

- PA 문제: `{YYYY-MM-DD}.json`, `{YYYY-MM-DD}_set{0,1,2}.json`
- Stream 문제: `stream_{YYYY-MM-DD}.json`
- 오늘 날짜 파일 없으면 최신 파일에서 검색

## 6. 분석 트래킹

- Event: Title Case (`Problem Solved`)
- Property: snake_case (`attempt_count`)
- 핵심 퍼널: Viewed → Attempted → Submitted → Solved

## 7. 주의사항

- 세션은 인메모리 (재시작 시 초기화)
- 스케줄러: 매일 오전 9시 자동 실행
- Gemini API 호출은 `api_usage` 테이블에 기록됨
- 포트: 백엔드 15174, 프론트엔드 15173

## 8. Implementation Plan 관리

- **저장 위치**: 작업 완료 후 implementation plan을 `docs/IMPLEMENTATION_PLAN.md`에 저장
- **목적**: 어느 컴퓨터에서 작업하든 최신 계획을 참고할 수 있도록 함
- **업데이트**: 새로운 기능/변경 계획 수립 시 기존 파일 업데이트 또는 교체
- **Git 커밋**: implementation plan 생성/수정 시 반드시 커밋하여 동기화

## 9. 문서 관리 및 지식 베이스 구조

모든 문서는 `docs/` 디렉토리 아래에 주제별로 관리하며, Wiki 형태의 구조를 유지한다.

### 핵심 문서 관리
- **[REFERENCE_WIKI.md](./docs/REFERENCE_WIKI.md)**: 서비스 철학, 전략(2-Track), 주요 기능 가이드 등 '비즈니스 및 사용자 중심' 사양 관리.
- **[TECH_WIKI.md](./docs/TECH_WIKI.md)**: 엔진 설계, 아키텍처, 배포 방법, 데이터 설계 등 '기술 및 구현 중심' 명세 관리.
- **주기적 업데이트**: 새로운 기능 구현 시 위 두 위키 중 적절한 곳에 기술 사양과 사용자 가이드를 반드시 추가/업데이트한다.

### 상태 및 프로세스 관리
- **[FUTURE_PLAN.md](./docs/FUTURE_PLAN.md)**: 로드맵 및 비전.
- **[TODO_LIST.md](./docs/TODO_LIST.md)**: 가동 중인 작업 및 단기 할 일.
- **[PATCH_NOTES.md](./docs/PATCH_NOTES.md)**: 완료된 작업의 이력 기록 (주요 마일스톤 완료 시 작성).

## 10. 회귀 방지 및 안정성 유지

새로운 기능 추가나 배포 시 핵심 기능(로그인, 문제 생성)이 중단되지 않도록 다음 수칙을 반드시 준수한다.

### 10.1 로그인 및 인증 보호
- `AuthContext.tsx`나 `LoginModal.tsx` 등 인증 관련 프론트엔드 코드 수정 시, 로그인 성공 후 `/auth/me`를 통한 유저 정보 동기화가 보장되는지 확인한다.
- 백엔드 인증 미들웨어(`require_user`, `require_admin`) 수정 시 기존 세션 방식과의 호환성을 테스트한다.

### 10.2 생성 파이프라인 무결성
- 문제 생성(`generator.py`) 및 데이터 생성 엔진 수정 시, 반드시 **통합 생성 로직(`adminApi.triggerNow`)**이 정상 작동하는지 먼저 검증한다.
- 파일 시스템(`problems/daily/`) 의존성보다는 **데이터베이스(Primary Source)** 저장을 우선시하여 환경 변화(Cloud Run 등)에 대응한다.

### 10.3 변경 전후 검증 (Verification)
- 배포 전 반드시 `verify` 스킬(테스트 및 빌드 체크)을 실행하여 기존 기능의 회귀 여부를 확인한다.
- 중요한 환경 변수나 DB 스키마 변경 시 `TECH_WIKI.md`에 즉시 반영하여 동기화 오류를 방지한다.

## 11. 관리자 기능 일원화 규칙

- **통합 우선**: 개별 데이터 생성, 개별 문제 생성 버튼보다는 모든 과정을 하나로 묶은 **'통합 생성'** 기능을 일차적으로 사용한다.
- **로직 분리**: 서비스 로직은 백엔드(`admin.py`, `generator.py`)에 집중시키고, 프론트엔드는 결과 표시와 트리거 역할만 수행한다.
- **명확한 피드백**: 생성 중인 상태, 성공 여부, 발생한 에러 메시지를 사용자에게 명확히 전달한다.
