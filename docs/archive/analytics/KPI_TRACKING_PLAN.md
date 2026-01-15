# 프로덕트 분석 트래킹 마스터 가이드 (KPI Tracking Plan)

이 문서는 QueryCraft의 성장 지표를 정의하고, 이를 측정하기 위한 트래킹 설계 및 관리 방법을 다루는 **데이터 거버넌스 가이드**입니다.

---

## 1. 분석 전략 (Strategy)

### 1.1 북극성 지표 (North Star Metric)
- **핵심 지표**: `Solved DAU`
- **정의**: 하루 동안 문제를 1회 이상 완결(Solved)한 고유 사용자 수.
- **의도**: 단순 방문이 아닌, 실제 SQL 실습을 통한 '가치 경험'을 최우선으로 측정합니다.

### 1.2 지표 트리 (KPI Tree)
1.  **유입 (Inflow)**: Signup Completed, Login Success
2.  **전환 (Conversion)**: Problem Attempted → Problem Submitted → **Problem Solved**
3.  **유지 (Retention)**: D1/D7 Retention, Habit Moment (3일 내 5문제 이상 해결)

---

## 2. 트래킹 설계 (Design)

### 2.1 이벤트 명명 규칙 (Taxonomy)
- **Event Name**: `Object + Action` 형태의 **Title Case** 사용 (예: `Problem Solved`)
- **Property Name**: **snake_case** 사용 (예: `attempt_count`, `time_spent_sec`)

### 2.2 핵심 유저 여정 (Funnel)
1.  **Page Viewed**: 서비스 탐색
2.  **Problem Viewed**: 문제 상세 확인 및 타이머 시작
3.  **Problem Attempted**: 첫 쿼리 실행/제출 시점 (최초 1회)
4.  **Problem Submitted**: 정답 확인 시도
5.  **Problem Solved** ⭐: 정답 달성 (핵심 액션)

---

## 3. 구현 상세 (Implementation)

모든 트래킹 로직은 [frontend/src/services/analytics.ts](../frontend/src/services/analytics.ts)에 캡슐화되어 있습니다.

### 3.1 사용자 식별 (Identify)
[AuthContext.tsx](../frontend/src/contexts/AuthContext.tsx)에서 로그인이 확인되는 즉시 실행됩니다.
```typescript
analytics.identify(user.id, {
    email: user.email,
    user_type: user.is_admin ? 'admin' : 'free',
    signup_date: user.created_at,
    current_level: user.level?.toString()
});
```

### 3.2 핵심 액션 트래킹
```typescript
// 문제 해결 시 (Workspace.tsx)
analytics.problemSubmitted(problemId, {
    isCorrect: true,
    difficulty: problem.difficulty,
    dataType: 'pa'
});
```

---

## 4. 데이터 거버넌스 (Governance)

### 4.1 Mixpanel Lexicon 관리
데이터 정합성을 위해 믹스패널의 **Lexicon(데이터 사전)**을 최신으로 유지해야 합니다.

1.  **CSV 준비**: `docs/mixpanel_final_events.csv` 및 `properties.csv`를 사용합니다.
2.  **업로드**: Mixpanel > Data Management > Lexicon 메뉴에서 Import 기능을 통해 업로드합니다.
3.  **업데이트**: 트래킹 계획 변경 시 `gen_lexicon.py`를 실행하여 CSV를 갱신한 뒤 다시 업로드합니다.

---

## 5. 용어 사전 (Glossary)
- **Distinct ID**: 사용자를 식별하는 고유 ID (`user_id`).
- **Property**: 이벤트와 함께 전송되는 메타데이터 (예: `problem_id`).
- **Habit Moment**: 유저가 서비스의 핵심 가치를 인지한 순간 (5문제 해결).

---

**데이터는 거짓말을 하지 않습니다. 정확한 트래킹으로 제품을 성장시켜주세요!**
