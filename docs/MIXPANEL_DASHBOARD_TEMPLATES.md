# Mixpanel Dashboard Templates for QueryCraft

이 문서는 QueryCraft에서 바로 적용할 수 있는 Mixpanel 대시보드 템플릿을 제공합니다. 각 템플릿은 **목표, 핵심 이벤트, 필터, 시각화 구성, 해석 포인트**로 구성됩니다.

## 1) 온보딩/유입 대시보드

**목표**
- 신규 사용자가 문제 풀이까지 얼마나 도달하는지 파악

**핵심 이벤트**
- `Page Viewed`
- `Problem Viewed`
- `Problem Attempted`
- `Problem Submitted`

**필터/세그먼트**
- `env` (local/staging/prod)
- `is_new_user`
- 유입 채널(추후 `utm_source` 등 추가 시)

**시각화 구성**
- Funnel: `Page Viewed` → `Problem Viewed` → `Problem Attempted` → `Problem Submitted`
- Trend: 일별 `Page Viewed` / `Problem Viewed`
- Table: 신규 유저 중 첫 문제 풀이까지 평균 시간

**해석 포인트**
- `Problem Viewed`까지 도달률이 낮으면 랜딩/내비게이션 이슈
- `Problem Attempted` 전환이 낮으면 난이도/문제 설명 품질 이슈

## 2) 문제 풀이 퍼널 대시보드 (Core Action)

**목표**
- 정답 도달(Problem Solved) 전환과 병목 파악

**핵심 이벤트**
- `Problem Viewed`
- `Problem Attempted`
- `Problem Submitted`
- `Problem Solved`
- `Problem Failed`

**필터/세그먼트**
- `difficulty_level` (easy/medium/hard)
- `data_type` (pa/rca/practice)
- `topic_tags`

**시각화 구성**
- Funnel: `Problem Viewed` → `Problem Attempted` → `Problem Submitted` → `Problem Solved`
- Trend: 난이도별 정답률(= Solved / Submitted)
- Distribution: 평균 시도 횟수 (`attempt_count`) 히스토그램

**해석 포인트**
- 난이도별 전환 하락 구간 확인
- 특정 `topic_tags`에서 이탈이 높으면 문제 품질 개선 필요

## 3) 리텐션/코호트 대시보드

**목표**
- 학습 지속성 및 개선 효과 확인

**핵심 이벤트**
- `Problem Solved` (또는 `Problem Attempted`)

**필터/세그먼트**
- `signup_cohort_date`
- `user_type` (free/admin)

**시각화 구성**
- Cohort: 첫 `Problem Solved` 날짜 기준 리텐션
- Trend: 주간 활성 사용자(WAU) vs 정답 사용자 수

**해석 포인트**
- 코호트별 리텐션 하락 시점 확인
- `Problem Attempted` 대비 `Problem Solved` 전환율 변화

## 4) RCA 분석 대시보드

**목표**
- RCA 문제 풀이 흐름과 이탈 구간 파악

**핵심 이벤트**
- `Problem Viewed`
- `Problem Attempted`
- `Problem Submitted`
- `Problem Solved`

**필터/세그먼트**
- `data_type = rca`
- `difficulty_level`

**시각화 구성**
- Funnel: RCA 전용 퍼널
- Trend: RCA 정답률 추이
- Bar: 난이도별 RCA 평균 풀이 시간

**해석 포인트**
- RCA 정답률이 급락하면 문제 설명 명확성 점검
- 특정 난이도에서 이탈 집중 시 난이도 재조정

## 5) AI Lab 사용성 대시보드

**목표**
- AI 기능이 학습 성과에 미치는 영향 확인

**핵심 이벤트**
- `SQL Executed`
- `Problem Submitted`
- `Problem Solved`
- `Translate` (Text-to-SQL 이벤트 필요)
- `AI Insight` (Insight 요청 이벤트 필요)

**필터/세그먼트**
- AI 기능 사용 유무 (event property 또는 user property)
- `data_type`

**시각화 구성**
- Trend: AI 기능 사용률
- Compare: AI 사용 vs 미사용 정답률
- Funnel: `Problem Attempted` → `Problem Solved` (AI 사용 유무 비교)

**해석 포인트**
- AI 사용자가 정답률/시간 효율이 유의미하게 높다면 기능 강조 UX 고려

## 6) 실험/버전 대시보드

**목표**
- 프롬프트/문제 생성 버전별 성능 비교

**핵심 이벤트**
- `Problem Viewed`
- `Problem Submitted`
- `Problem Solved`

**필터/세그먼트**
- `prompt_version`
- `experiment_group`

**시각화 구성**
- Funnel: 그룹별 전환율
- Trend: 그룹별 정답률 추이

**해석 포인트**
- 그룹 간 성과 차이가 뚜렷하면 실험 결과 반영

---

## Mixpanel 리포트 설정 단계 (화면 기준)

### 공통 준비

1. Mixpanel 프로젝트에서 `Events` 탭을 열어 이벤트 수집이 정상인지 확인합니다.
2. `Properties`에서 `env`, `data_type`, `difficulty_level` 등 핵심 속성이 들어오는지 확인합니다.
3. 대시보드에서 기본 필터로 `env=prod`를 추가합니다.

### Funnel 리포트 생성

1. `Create Report` → `Funnel` 선택
2. 이벤트 순서를 지정 (예: `Problem Viewed` → `Problem Attempted` → `Problem Submitted` → `Problem Solved`)
3. `Conversion Window`를 1~7일로 설정
4. 세그먼트/필터 추가 (예: `data_type=pa`, `difficulty_level=hard`)
5. 완료 후 리포트를 저장하고 대시보드에 고정

### Retention 리포트 생성

1. `Create Report` → `Retention` 선택
2. First Event: `Problem Solved` (또는 `Problem Attempted`)
3. Returning Event: 동일 이벤트 또는 `Problem Solved`
4. Cohort 기준을 `signup_cohort_date` 또는 첫 문제 풀이일로 설정
5. `Weekly` 또는 `Daily`로 기간을 맞추고 대시보드에 추가

### Cohort 리포트 생성

1. `Create Report` → `Cohort` 선택
2. 조건: `Problem Solved` 1회 이상
3. 세그먼트: `difficulty_level`, `data_type`, `prompt_version`
4. 코호트를 저장하고 다른 리포트 필터에 연결

### Trend 리포트 생성

1. `Create Report` → `Insights/Trends` 선택
2. Metric: `Problem Solved` (count)
3. Breakdown: `difficulty_level` 또는 `data_type`
4. Time range를 7/30/90일로 바꿔 추세 확인
5. 대시보드에 추가해 운영용 지표로 고정

## 권장 운영 팁

- 모든 대시보드는 기본적으로 `env=prod` 필터를 적용합니다.
- 신규 기능은 이벤트 정의 후 1~2일간 수집 안정화 기간을 둡니다.
- Mixpanel Live View로 이벤트 페이로드를 먼저 확인한 뒤 대시보드에 적용합니다.
