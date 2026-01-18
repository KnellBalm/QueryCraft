# QueryCraft Patch Notes

> **목적**: TODO List에서 완료된 작업들을 아카이브하고, 서비스의 발전 과정을 기록하는 문서입니다.

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
*마지막 업데이트: 2026-01-18*
