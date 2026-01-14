---
trigger: always_on
description: SQL Labs 프로젝트 작업 시 항상 참고하는 규칙
---

# QueryCraft 프로젝트 작업 규칙

## 0. 구현계획
구현 계획이나 설명은 항상 한글로 할 것

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