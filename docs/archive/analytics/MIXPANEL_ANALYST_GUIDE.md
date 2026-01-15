# Mixpanel Analyst Guide for QueryCraft

이 문서는 QueryCraft에서 Mixpanel을 활용해 **PA(제품 분석) 관점의 데이터 분석 업무**를 수행하는 방법을 정리합니다. 개발이 아니라 **분석가 실무 기준**으로 작성했으며, 이벤트 설계/대시보드/지표 운영을 포함합니다.

## 1) QueryCraft의 분석 목적 요약

QueryCraft의 핵심 목표는 **사용자가 SQL 문제를 풀며 학습 성과를 올리는 것**입니다. 따라서 Mixpanel 분석의 핵심은 다음 질문에 답하는 것입니다.

- 사용자는 **어떤 경로로 유입**되었는가?
- 어떤 문제가 **가장 많은 이탈**을 유발하는가?
- 사용자가 **정답(Problem Solved)**까지 도달하는 확률은 어떤가?
- 어떤 기능이 **학습 성과(리텐션/정답률)**에 영향을 주는가?
- AI 기능(Text-to-SQL, Insight)이 **문제 해결에 실제로 도움이 되는가?**

## 2) Mixpanel에서 다루는 주요 이벤트

QueryCraft는 `frontend/src/services/analytics.ts`에서 이벤트를 정의합니다. 분석가가 주로 보는 핵심 이벤트는 다음과 같습니다.

- `Page Viewed`
- `Problem Viewed`
- `Problem Attempted`
- `Problem Submitted`
- `Problem Solved` (Core Action)
- `Problem Failed`
- `Hint Requested`
- `SQL Executed`
- `SQL Error Occurred`
- `Tab Changed`

AI Lab 연계 이벤트는 다음과 같은 흐름으로 파생됩니다.

- `SQL Executed` → `AI Insight` (insight 요청 시점)
- `Translate` (Text-to-SQL 호출 시점)

필요 시 `docs/EVENT_TRACKING_GUIDE.md`에 이벤트 스펙을 동기화해야 합니다.

## 3) 핵심 대시보드 구성 (PA 관점)

### 3.1 온보딩/유입 대시보드

목표: 신규 사용자가 문제 풀이까지 도달하는 비율을 확인

- Funnel: `Page Viewed` → `Problem Viewed` → `Problem Attempted` → `Problem Submitted`
- 세그먼트: 유입 경로, 신규/기존 사용자, 국가/언어
- KPI: 첫 문제 도달률, 첫 제출까지 시간

### 3.2 문제 풀이 퍼널 대시보드

목표: 문제 풀이 전환과 병목 파악

- Funnel: `Problem Viewed` → `Problem Attempted` → `Problem Submitted` → `Problem Solved`
- 세그먼트: 난이도, 데이터 타입(pa/rca), topic, weekday/weekend
- KPI: 정답률, 평균 시도 횟수, 평균 시간

### 3.3 리텐션/코호트 대시보드

목표: 학습 지속성 및 개선 효과 확인

- Cohort 기준: 가입일, 첫 문제 풀이일, 첫 정답일
- 행동 기준: `Problem Solved` 또는 `Problem Attempted`
- KPI: D1/D7/D30 리텐션, 코호트별 정답률 변화

### 3.4 RCA 분석 대시보드

목표: RCA 문제의 난이도/이탈 구간 파악

- Funnel: `Problem Viewed` → `Problem Attempted` → `Problem Submitted` → `Problem Solved`
- 세그먼트: data_type = rca, difficulty
- KPI: RCA 전환율, RCA 이탈률, RCA 평균 풀이 시간

### 3.5 AI Lab 기능 대시보드

목표: AI 기능의 실질적 효과 확인

- Text-to-SQL 사용률
  - 세그먼트: 사용 유무
  - KPI: 사용 시 정답률 상승 여부, 평균 풀이 시간 변화
- AI Insight 사용률
  - KPI: Insight 사용 후 재도전율/정답률 변화

## 4) 분석가가 해야 하는 실무 업무 목록

### 4.1 이벤트 거버넌스

- 이벤트/속성 네이밍 룰 유지
- 중복 이벤트 제거
- 스키마 변경 시 문서와 동기화

### 4.2 데이터 품질 점검

- 누락 이벤트 탐지 (특정 페이지에서 이벤트 미발생)
- 중복 이벤트 탐지 (double firing)
- 속성 누락/형식 오류 (예: 날짜 포맷)
- data_type 오기입 여부

### 4.3 실험(A/B) 분석 준비

현재는 실험 실행이 없지만, 다음 속성을 활용할 수 있도록 설계되어 있습니다.

- `prompt_version`
- `experiment_group`

A/B 테스트 시 Mixpanel에서 **group별 퍼널/리텐션 비교**가 가능하도록 설정하는 것이 중요합니다.

### 4.4 세그먼트/페르소나 정의

추천 세그먼트:

- 신규 유저 vs 기존 유저
- 정답률 상위 20% vs 하위 20%
- 힌트 사용 유무
- AI 기능 사용 유무

## 5) QueryCraft에서 추천하는 핵심 KPI

- **Core Action**: Problem Solved
- **전환 KPI**: Viewed → Submitted 전환율
- **효율 KPI**: 평균 풀이 시간, 평균 시도 횟수
- **성장 KPI**: D7 리텐션, 주간 정답률 상승률

## 6) 실무 분석 Workflow (예시)

1. 오늘 신규 유저가 감소 → 유입 Funnel 확인
2. `Problem Viewed`는 유지, `Problem Attempted`가 하락 → 문제 난이도 상승 의심
3. difficulty=hard 세그먼트로 분리 → 특정 토픽에서 급락 확인
4. RCA 분석 문제에서 이탈이 집중 → 문제 문구 개선 필요
5. AI Lab 기능 사용 유저가 정답률이 높음 → 기능 강조 UX 실험 제안

## 7) Mixpanel 운영 체크리스트

- [ ] 이벤트 정의 문서 최신화 (`docs/EVENT_TRACKING_GUIDE.md`)
- [ ] 신규 기능 배포 시 이벤트 누락 여부 점검
- [ ] Mixpanel Live View에서 이벤트 수집 확인
- [ ] 주요 퍼널/리텐션 대시보드 유지보수
- [ ] 실험 그룹 분기 속성 검증

## 8) 연결된 코드 위치

- 이벤트 정의: `frontend/src/services/analytics.ts`
- 이벤트 사용 위치: `frontend/src/pages/Workspace.tsx`
- 이벤트 문서: `docs/EVENT_TRACKING_GUIDE.md`

---

필요 시 이 문서를 기반으로 **대시보드 템플릿**이나 **분석 쿼리 예시**도 추가할 수 있습니다.
