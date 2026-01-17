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


## 🚀 Upcoming Tasks

### 🎨 Claude (Frontend Refactoring)

- [ ] `App.tsx` (1,100줄) 분리: `AdminPage`, `StatsPage`, `AdaptiveTutor` 등으로 컴포넌트화
- [ ] GNB(Global Navigation Bar) 디자인 고도화 (Glassmorphism 적용)

- [ ] **Data Pipeline**: DuckDB 기반의 대용량 이벤트 분석 파이프라인 고도화
- [ ] **Legacy API 정리**: Phase 1 migration (레거시 엔드포인트 제거 계획 수립)

## 🧪 Verification Plan

- **Automated**: GitHub Actions를 통한 `pytest` 전수 검사
- **Manual**: 다크모드 및 모바일 반응형 디자인 최종 확인
