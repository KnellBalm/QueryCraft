# QueryCraft 분석 가이드

> 이 문서는 QueryCraft의 **이벤트 트래킹, KPI, 대시보드 운영**을 위한 통합 가이드입니다.

---

## 1. 분석 전략 (Strategy)

### 1.1 북극성 지표 (North Star Metric)
- **핵심 지표**: `Solved DAU`
- **정의**: 하루 동안 문제를 1회 이상 완결(Solved)한 고유 사용자 수
- **의도**: 단순 방문이 아닌, 실제 SQL 실습을 통한 '가치 경험'을 최우선으로 측정

### 1.2 지표 트리 (KPI Tree)
1. **유입 (Inflow)**: Signup Completed, Login Success
2. **전환 (Conversion)**: Problem Attempted → Problem Submitted → **Problem Solved**
3. **유지 (Retention)**: D1/D7 Retention, Habit Moment (3일 내 5문제 이상 해결)

---

## 2. 이벤트 스펙 (Event Specification)

### 2.1 명명 규칙 (Taxonomy)
- **Event Name**: `Object + Action` 형태의 **Title Case** (예: `Problem Solved`)
- **Property Name**: **snake_case** (예: `attempt_count`, `time_spent_sec`)

### 2.2 핵심 유저 퍼널
```
Page Viewed → Problem Viewed → Problem Attempted → Problem Submitted → Problem Solved ⭐
```

### 2.3 핵심 이벤트 목록

| 이벤트 명 | 발생 시점 | 용도 |
|:---|:---|:---|
| `Page Viewed` | 페이지 로드 시 | 트래픽 분석 |
| `Problem Viewed` | 문제 상세 진입 시 | 문제 도달률 측정 |
| `Problem Attempted` | 문제에서 첫 쿼리 실행/제출 시 | 풀이 시작율 측정 |
| `SQL Executed` | 실행 버튼 클릭 시 | SQL 복잡도 및 시도 횟수 분석 |
| `Problem Submitted` | 정답 확인 버튼 클릭 시 | 제출율 측정 |
| `Problem Solved` ⭐ | 정답 판정 시 | **북극성 지표 (핵심 전환)** |
| `Problem Failed` | 오답 판정 시 | 오답률 분석 |
| `Hint Requested` | 힌트 버튼 클릭 시 | 문제 난이도 및 허들 분석 |
| `Tab Changed` | 탭 변경 시 | UI 사용 패턴 |
| `Login Success` | 로그인 완료 시 | 인증 퍼널 |
| `Sign Up Completed` | 회원가입 완료 시 | 인증 퍼널 |

---

## 3. 구현 가이드 (Implementation)

### 3.1 아키텍처 개요
```text
[React Components] 
      │
      ▼
[services/analytics.ts] ◀── 싱글톤 객체 (Single Source of Truth)
      │
      ├─▶ Mixpanel (이벤트 분석)
      ├─▶ PostHog (세션 녹화 및 히트맵)
      └─▶ GA4/GTM (광고 및 유입 분석)
```

### 3.2 환경 변수 (`.env`)
```bash
VITE_MIXPANEL_TOKEN=...
VITE_POSTHOG_KEY=...
VITE_POSTHOG_HOST=https://us.i.posthog.com
```

### 3.3 이벤트 전송 예시
```typescript
import { analytics } from '../services/analytics';

// 1. 페이지 조회
analytics.pageView('PracticePage');

// 2. 문제 선택
analytics.problemViewed(problemId, { 
    difficulty: 'medium', 
    dataType: 'pa' 
});

// 3. SQL 실행
analytics.sqlExecuted(problemId, {
    sql: sqlText,
    hasError: !!error,
    errorMessage: error?.message
});

// 4. 정답 제출 (Core Action)
analytics.problemSubmitted(problemId, {
    isCorrect: true,
    difficulty: 'medium',
    dataType: 'pa'
});
```

### 3.4 사용자 식별 (Identify)
```typescript
// AuthContext.tsx
analytics.identify(user.id, {
    email: user.email,
    user_type: user.is_admin ? 'admin' : 'free',
    signup_date: user.created_at,
    current_level: user.level?.toString()
});
```

### 3.5 디버깅 방법
1. **브라우저 콘솔**: `analytics.setDebugMode(true)` 설정 시 모든 이벤트 로그 출력
2. **Network 탭**: `api.mixpanel.com` 또는 `app.posthog.com`으로 나가는 페이로드 확인
3. **Mixpanel Live View**: 실시간 이벤트 수집 확인

---

## 4. 대시보드 템플릿 (Dashboard Templates)

### 4.1 온보딩/유입 대시보드

**목표**: 신규 사용자가 문제 풀이까지 도달하는 비율 파악

| 항목 | 설정 |
|------|------|
| Funnel | `Page Viewed` → `Problem Viewed` → `Problem Attempted` → `Problem Submitted` |
| 필터 | `env` (local/staging/prod), `is_new_user` |
| KPI | 첫 문제 도달률, 첫 제출까지 시간 |

**해석 포인트**:
- `Problem Viewed`까지 도달률이 낮으면 랜딩/내비게이션 이슈
- `Problem Attempted` 전환이 낮으면 난이도/문제 설명 품질 이슈

### 4.2 문제 풀이 퍼널 대시보드 (Core Action)

**목표**: 정답 도달(Problem Solved) 전환과 병목 파악

| 항목 | 설정 |
|------|------|
| Funnel | `Problem Viewed` → `Problem Attempted` → `Problem Submitted` → `Problem Solved` |
| 세그먼트 | `difficulty_level`, `data_type` (pa/rca/practice), `topic_tags` |
| KPI | 정답률, 평균 시도 횟수, 평균 풀이 시간 |

**해석 포인트**:
- 난이도별 전환 하락 구간 확인
- 특정 `topic_tags`에서 이탈이 높으면 문제 품질 개선 필요

### 4.3 리텐션/코호트 대시보드

**목표**: 학습 지속성 및 개선 효과 확인

| 항목 | 설정 |
|------|------|
| 리텐션 이벤트 | `Problem Solved` (또는 `Problem Attempted`) |
| 코호트 기준 | `signup_cohort_date`, 첫 문제 풀이일 |
| 세그먼트 | `user_type` (free/admin) |
| KPI | D1/D7/D30 리텐션 |

### 4.4 RCA 분석 대시보드

**목표**: RCA 문제 풀이 흐름과 이탈 구간 파악

| 항목 | 설정 |
|------|------|
| 필터 | `data_type = rca` |
| Funnel | RCA 전용 퍼널 |
| KPI | RCA 정답률, RCA 평균 풀이 시간 |

### 4.5 AI Lab 사용성 대시보드

**목표**: AI 기능이 학습 성과에 미치는 영향 확인

| 항목 | 설정 |
|------|------|
| 세그먼트 | AI 기능 사용 유무 |
| 비교 | AI 사용 vs 미사용 정답률 |
| KPI | Text-to-SQL 사용률, Insight 사용 후 재도전율 |

---

## 5. 데이터 거버넌스 (Governance)

### 5.1 Mixpanel Lexicon 관리
1. **CSV 준비**: `docs/mixpanel_final_events.csv` 및 `mixpanel_final_properties.csv`
2. **업로드**: Mixpanel > Data Management > Lexicon에서 Import
3. **업데이트**: 트래킹 계획 변경 시 CSV 갱신 후 다시 업로드

### 5.2 데이터 품질 점검
- [ ] 누락 이벤트 탐지 (특정 페이지에서 이벤트 미발생)
- [ ] 중복 이벤트 탐지 (double firing)
- [ ] 속성 누락/형식 오류 (예: 날짜 포맷)
- [ ] data_type 오기입 여부

### 5.3 운영 체크리스트
- [ ] 신규 기능 배포 시 이벤트 누락 여부 점검
- [ ] Mixpanel Live View에서 이벤트 수집 확인
- [ ] 주요 퍼널/리텐션 대시보드 유지보수
- [ ] 기본 필터로 `env=prod` 적용

---

## 6. 용어 사전 (Glossary)

| 용어 | 설명 |
|------|------|
| Distinct ID | 사용자를 식별하는 고유 ID (`user_id`) |
| Property | 이벤트와 함께 전송되는 메타데이터 (예: `problem_id`) |
| Habit Moment | 유저가 서비스의 핵심 가치를 인지한 순간 (5문제 해결) |
| Core Action | 핵심 전환 행동 (Problem Solved) |

---

## 7. 코드 위치 참조

| 영역 | 파일 경로 |
|------|----------|
| 이벤트 정의 | `frontend/src/services/analytics.ts` |
| 이벤트 사용 | `frontend/src/pages/Workspace.tsx` |
| Lexicon 데이터 | `docs/mixpanel_final_events.csv`, `docs/mixpanel_final_properties.csv` |
| 원본 문서 | `docs/archive/analytics/` |

---

**모든 사용자 행동은 측정 가능해야 하며, 측정된 데이터는 제품 개선의 근거가 됩니다.**
