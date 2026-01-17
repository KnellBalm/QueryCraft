# QueryCraft Phase 2: Security, Reliability, and Refactoring Plan

## 🎯 Goal

QueryCraft의 상용 출시를 위해 보안을 강화하고, 테스트 자동화를 통해 신뢰성을 확보하며, 유지보수가 용이하도록 코드를 리팩토링합니다.

## ✅ Completed Tasks (Antigravity)

### 1. 보안 강화 (Security Hardening)

- **비밀번호 정책**: 최소 8자, 대소문자, 숫자, 특수문자 포함 필수 조건 적용
- **Rate Limiting**: 로그인 시도 제한 (10분 내 5회 실패 시 차단) 기능을 DB(`login_attempts`) 기반으로 구현
- **Admin 관리**: 하드코딩된 이메일을 환경 변수(`ADMIN_EMAILS`)로 전환

### 2. 테스트 수정 및 신뢰성 확보

- **101개 테스트 통과**: 실패하던 11개 테스트를 전수 조사하여 수정 완료
- **API 경로 수정**: `/auth` 등 레거시 경로를 `/api/auth`로 통일
- **데이터 검증**: `ISO 8601` 날짜 포맷팅 및 공백 포함 문자열 비교 로직 개선
- **CI 연동**: `ci.yml`을 업데이트하여 모든 백엔드 테스트(`pytest tests/`)가 자동 실행되도록 설정

### 3. 인프라 및 기타 최적화

- **DB 풀 최적화**: Supabase Free Tier 환경을 고려하여 `maxconn`을 5로 조정
- **UX 개선**: 주말 접속 제한 화면에 '연습 모드' 링크 추가 및 CSS 스타일링 반영
- **Adaptive Tutor (P1)**: `user_skills` 및 `problems` 스키마 고도화, 역량 분석 알고리즘 및 취약점 기반 추천 엔진 구현 완료

### 4. 프론트엔드 리팩토링 및 UI 완성 (Claude)

- **App.tsx 분리**: 1,100줄의 `App.tsx`를 `Workspace`, `Practice`, `StatsPage`, `AdminPage` 등 페이지 단위로 모듈화하여 유지보수성 향상
- **GNB 고도화**: Glassmorphism 디자인 및 'Core Skills', 'Future Lab' 2트랙 시스템 구현
- **Adaptive Tutor UI 연동**: 레이더 차트 시각화, 취약점 기반 맞춤형 추천 배지, 전용 튜터링 가이드 페이지 구현 완료

### 5. RCA 시나리오 고도화 (Antigravity & Claude)

- **이상 데이터 주입**: 리텐션 급락, 가입 전환 하락 등 실무형 장애 시나리오 3종 추가 (`anomaly_injector.py`)
- **AI 힌트 고도화**: 분석 단계를 안내하는 단계별(Staged) 힌트 시스템 및 AI 프롬프트 연동 (`prompt_rca.py`)
- **RCA 전용 UI**: 이상 현상 브리핑 섹션 및 단계별 힌트 아코디언, 분석 리포트 마크다운 템플릿 복사 기능 구현
- **관리자 도구**: 특정 장애 시나리오를 즉시 트리거하여 연습 문제를 생성할 수 있는 관리자 API 추가

41: ### 6. Cloud Run Worker 안정화 (Antigravity)
42: - **의존성 동기화**: `worker/requirements.txt`를 루트와 동기화하여 임포트 에러 방지
43: - **로깅 및 예외 처리**: 컨테이너 시작 시 상세 로깅 및 `main` 함수 try-except 래핑으로 장애 원인 파악 용이성 확보
44: - **인프라 최적화**: 워커 메모리 상향(1Gi) 및 Docker 실행 방식을 모듈 모드(`-m`)로 변경하여 안정성 강화

### 🚀 Upcoming Tasks

- [ ] **AI 인사이트 리포트**: SQL 실행 결과에 대한 자동 분석 및 요약 리포트 생성 기능
- [ ] **MCP 연동**: Cursor/Claude Desktop 등 외부 IDE에서 QueryCraft 데이터 및 문제에 접근 가능한 MCP 서버 구축
- [ ] **Data Pipeline**: DuckDB 기반의 대용량 이벤트 분석 파이프라인 고도화

## 🧪 Verification Plan

- **Automated**: GitHub Actions를 통한 `pytest` 전수 검사
- **Manual**: 다크모드 및 모바일 반응형 디자인 최종 확인
