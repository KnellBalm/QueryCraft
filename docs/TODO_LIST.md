# QueryCraft TODO List

> **목적**: 서비스 비전 실현을 위해 당장 수행해야 할 작업 목록입니다. 에이전트와 대화하며 작업을 진행할 때 이 문서의 항목을 기준으로 소통합니다.

---

## 🔥 P0: 핵심 시스템 안정화 및 배포
- [ ] **MixPanel 이벤트 검증**
  - [ ] 프로덕션 토큰 분리 및 정상 수집 완료 확인
  - [ ] Mixpanel Live View에서 데이터 실시간 수집 확인
- [ ] **Cloud Scheduler 추가 알림 구성 (선택)**
  - [ ] Cloud Logging 기반 실패 알림 규칙 생성
  - [ ] Slack 또는 이메일 연동

---

## 🚀 P1: 신규 기능 구현 (Phase 3)

### 7. AI 인사이트 리포트 자동화 (Upcoming)
- [ ] SQL 결과 → AI 분석 파이프라인 설계
- [ ] 인사이트 리포트 출력 형식 정의 (Key Findings, Action Items)
- [ ] `/api/ai/insight` 엔드포인트 구현 (Gemini API 연동)
- [ ] 프론트엔드 AI 인사이트 패널 컴포넌트 개발

### 9. Text-to-SQL 보조 도구 (Upcoming)
- [ ] 자연어 질문 → SQL 초안 생성 로직 설계
- [ ] `/api/ai/translate` 고도화 (스키마 컨텍스트 주입)
- [ ] SQL 에디터 상단 자연어 입력 및 자동 삽입 UI 구현

---

## 🛠️ P2: 고도화 및 인프라 개선

### 10. MCP (Model Context Protocol) 연동
- [ ] `mcp-python-sdk`를 활용한 기본 DB 조회 도구 구현
- [ ] AI 힌트 시스템에 MCP 실시간 데이터 조회 연동
- [ ] Cursor IDE / Claude Desktop 연동 테스트

### 분석 및 운영
- [ ] Mixpanel 대시보드 설정 (Funnel, Retention, Flow 분석용)
- [ ] [C] `docs/ANALYTICS_GUIDE.md` 최신 이벤트 목록 업데이트

---
*마지막 업데이트: 2026-01-18*
