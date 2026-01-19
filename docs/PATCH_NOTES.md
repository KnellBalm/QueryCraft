# QueryCraft Patch Notes

> **목적**: TODO List에서 완료된 작업들을 아카이브하고, 서비스의 발전 과정을 기록하는 문서입니다.

---

## [2026-01-19] 통합 Generator 아키텍처 구축 완료

### 🌌 Backend: 통합 문제 생성 엔진
- **단일 엔트리 포인트**: `problems.generator.generate(mode="pa"|"stream"|"rca")` 통합 인터페이스 구현
- **프롬프트 시스템 통합**:
  - `problems/prompt.py`에 mode별 동적 프롬프트 선택 로직 추가
  - `problems/prompt_stream.py` 생성: Stream 데이터 요약 및 프롬프트 로직 이동
  - PA/Stream/RCA 모두 단일 `build_prompt(mode)` 호출로 처리
- **동적 세트 수 관리**: PA는 2세트(12문제), Stream/RCA는 1세트(6문제) 자동 결정
- **하위 호환성**: `generator_stream.py`에 deprecated 경고 추가, 기존 코드 유지

### 🛡️ 안정성 및 Cloud Run 최적화
- **파일 경로 에러 원천 차단**:
  - `ensure_dir()` 헬퍼 함수로 디렉토리 생성 보장
  - `safe_save_json()` 함수로 파일 저장 실패 시 warning 처리 (중단하지 않음)
  - DB 저장 실패 시에도 파일 저장 시도하여 데이터 손실 방지
- **Cloud Run 환경 대응**:
  - `K_SERVICE` 환경 변수로 Cloud Run 감지
  - 휘발성 파일 시스템에서도 안정적 동작 (DB-first 아키텍처)
  - PostgreSQL을 Primary Source로 명시

### 🔧 관리자 API 통합
- **`/admin/trigger/daily-generation`**: 통합 generator 사용 (PA + Stream 순차 생성)
- **`/admin/generate-problems`**: 모든 mode (pa/stream/rca) 단일 엔드포인트로 통합
- **`/admin/trigger-now`**: 통합 생성 파이프라인 (데이터 + PA + Stream)

### 📊 프론트엔드 통합 상태 확인
- **이미 통합 완료 확인**:
  - App.tsx: Track 기반 네비게이션 (Core Skills ↔ Future Lab)
  - MainPage.tsx: "오늘의 일일 분석" 단일 카드 (PA + STREAM 태그)
  - /pa, /stream 개별 메뉴 없음 (legacy redirect 유지)

### 📝 기술 부채 정리
- **코드 중복 제거**: `get_expected_result()`, `save_problems_to_db()` 중복 제거
- **일관된 네이밍**: mode 파라미터 표준화 ("pa"|"stream"|"rca")
- **마이그레이션 가이드**: 기존 코드 → 통합 generator 전환 가이드 제공

---

## [2026-01-18] 서비스 안정화 및 UI 개선
### 🔐 보안 및 로컬 환경 안정화
- **Supabase DB 연결 이슈 해결**: IPv6 미지원 환경을 위한 Connection Pooler (`aws-1-ap-northeast-2`) 연동 성공.
- **인증 시스템**: 관리자 계정(`admin@querycraft.kr`) 생성 및 로그인 기능 정상화.
- **백엔드 로깅**: 로그 폴더 권한 오류(`Permission denied`) 해결 및 안정화.
- **DB 최적화**: Supabase 접속 세션 효율화 (`maxconn=5`).

### 🎨 프론트엔드 UI/UX
- **GNB 메뉴 정리**: "오늘의 학습" 드롭다운을 제거하고 Daily Challenge 접근성 강화.
- **로그인 오류 수정**: Nginx 프런트엔드 프록시 설정 오류(API 프리픽스 유실) 수정.

---

## [2026-01-17] Daily Challenge 시스템 구축 및 Cloud Scheduler 연동
### 🗓️ Daily Challenge MVP (95% 완료)
- **Backend**: 시나리오, 데이터, 문제 자동 생성 엔진(`scenario_generator` 등) 구현.
- **API**: `/api/daily/*` 엔드포인트 5종 구축.
- **Frontend**: ScenarioPanel 및 DailyChallenge 전용 페이지 개발.
- **Worker**: 배포 효율을 위한 통합 빌드 인프라 구축.

### ⏰ Cloud Scheduler & 스케줄러 개선
- **GCP 연동**: Cloud Scheduler (`querycraft-daily-generation`) 생성 및 OIDC 인증 설정.
- **엔드포인트**: `/admin/schedule/run`을 통한 강제 실행 및 자동화 로직 구현.
- **안정성**: `ENABLE_SCHEDULER` 환경변수 제어 및 중복 실행 방지 기능 추가.

---

## [2026-01-16] 초기 보안 강화 및 인프라 구축
### 🛡️ 보안 핵심
- **비밀번호 정책**: 최소 8자, 대소문자/숫자/특수문자 조합 필수화.
- **인증 보안**: Rate Limiting (10분 내 5회 실패 시 차단) 구현.
- **테스트**: 백엔드 유닛 테스트 101개 전 항목 통과 달성.

### 📈 분석 트래킹
- **Mixpanel**: AI 사용 임계치 이벤트 트래킹 추가 및 기초 설계 완료.

---

## [이전 내역]
- API 에러 해결 (Leaderboard 500, Recommend 400, Translate 404 해결)
- Phase 1 & 2 핵심 로직 기반 구축 완료

---
*마지막 업데이트: 2026-01-19*
