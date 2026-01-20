# QueryCraft TODO List

> **목적**: 서비스 비전 실현을 위해 당장 수행해야 할 작업 목록입니다. 에이전트와 대화하며 작업을 진행할 때 이 문서의 항목을 기준으로 소통합니다.

---

## 🔥 P0: 통합 동적 생성 및 UI/UX 대개편 (현재 진행 중)

### 🌌 Antigravity (엔진, 인프라 및 프리미엄 UI)
- [x] **Phase 2 & 3: 엔진 고도화 및 철벽 방어** ✅ (2026-01-19 완료)
  - [x] `generator.py` 통합 구현 및 Stream 특화 처리
    - `problems.generator.generate(mode="pa"|"stream"|"rca")` 단일 엔트리 구현
    - `prompt.py`에 stream 모드 지원 추가 (`build_prompt(mode="stream")`)
    - PA: 2세트(12문제), Stream/RCA: 1세트(6문제) 동적 처리
  - [x] `[Errno 2]` 오류 방지: 모든 파일 쓰기에 try-except/mkdir 보장
    - `ensure_dir()` 헬퍼 함수 추가
    - `safe_save_json()` 파일 저장 안전성 강화
    - DB 저장 실패 시에도 파일 저장 시도 (데이터 손실 방지)
  - [x] Cloud Run 환경 감지 → DB-only 모드 자동 전환
    - `K_SERVICE` 환경 변수로 Cloud Run 감지
    - 파일 저장 실패 시 warning으로 처리 (중단하지 않음)
    - PostgreSQL을 primary source로 명시
- [x] **프론트엔드 UI/UX 대개편 (Arcade Lobby)** ✅ (기완료)
  - [x] `App.tsx`: 라우팅 통합 완료
    - Track 기반 네비게이션 (Core Skills ↔ Future Lab)
    - /pa, /stream 개별 메뉴 없음 (통합됨)
    - Legacy redirect 유지 (/pa → /workspace/pa)
  - [x] `MainPage.tsx`: 아케이드 카드 단일화 완료
    - "오늘의 일일 분석" 단일 카드 (PA + STREAM 태그)
    - 동적 산업군/회사명 표시
    - Track별 게임 모드 분리 (Core/Future)
- [x] **Phase 4: 관리자 API 통합** ✅
  - [x] `/admin/trigger/daily-generation`: 통합 generator 사용
  - [x] `/admin/generate-problems`: 모든 mode (pa/stream/rca) 통합
  - [x] `/admin/trigger-now`: 통합 생성 파이프라인

### 🤖 Claude (프롬프트 및 분석 설계)
- [x] **Phase 1: 프롬프트 시스템 통합** ✅ (2026-01-19 완료)
  - [x] `problems/prompt_stream.py` 생성 및 `get_stream_data_summary()` 구현
  - [x] `prompt.py::build_prompt(mode)` 확장 (pa/stream/rca 지원)
  - [x] `generator_stream.py` deprecated 처리 (하위 호환성 유지)
- [x] **문서화**: `TECH_WIKI.md` 및 `PATCH_NOTES.md` 업데이트 ✅ (2026-01-19 완료)
  - [x] PATCH_NOTES.md: 2026-01-19 통합 Generator 아키텍처 엔트리 추가
  - [x] TECH_WIKI.md: Section 1.2 통합 Generator 아키텍처 상세 설명 추가
  - [x] 호출 인터페이스, 내부 흐름, 안정성 강화 사항 문서화
- [ ] **디자인**: 아케이드 로비 스타일 가이드 준수 여부 체크

---

## 🔥 P0: 데일리 챌린지 운영 및 AI 어시스턴트 고도화 (현재 집중)

### 🌌 핵심 기능 안정성 유지 (Frozen Core)
- [x] **Stable Milestone 1.0**: 에디터, 채점, 제출 로직 보호 완료
- [ ] 정기적인 DB 백업 및 로그 모니터링

### 🤖 AI 어시스턴트 (힌트 & 도와줘요)
- [ ] `ai_service.py::get_ai_help` 프롬프트 정교화 (더 친절하고 단계적인 힌트)
- [ ] 문제별 오답 패턴에 기반한 동적 힌트 생성 로직 검토
- [ ] AI 도움말 사용 시 Mixpanel 이벤트 트래킹 강화

### 📈 분석 및 퍼널 최적화 (Mixpanel)
- [ ] **핵심 퍼널**: 접속 → 문제 조회 → 시도 → AI 힌트 사용 → 제출 → 정답
- [ ] AI 힌트가 전환율(정답률)에 미치는 영향 분석 대시보드 구축

---

## 💤 P1: 일시 중단 및 보류 (Future expansion)
- [ ] **AI 인사이트 리포트**: 쿼리 결과 분석 (당분간 보류)
- [ ] **Text-to-SQL**: 자연어 쿼리 작성 (보조 도구로만 유지)
- [ ] **RCA 시뮬레이터**: 고도화 보류
- [ ] **MCP 연동**: 향후 확장 과제로 유지

---
*마지막 업데이트: 2026-01-21 (백엔드 통합 생성기 완료)*
