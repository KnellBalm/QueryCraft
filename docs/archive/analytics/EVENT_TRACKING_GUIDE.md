# 이벤트 트래킹 구현 가이드

본 문서는 QueryCraft의 프론트엔드에서 Mixpanel, PostHog, GA4(GTM)로 이벤트를 전송하는 기술적 구현 방식을 설명합니다.

---

## 1. 아키텍처 개요

QueryCraft는 다중 분석 도구를 지원하기 위해 **추상화 레이어(analytics.ts)**를 사용합니다.

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

---

## 2. 주요 연동 도구 설정

### 2.1 환경 변수 (`.env`)
```bash
VITE_MIXPANEL_TOKEN=...
VITE_POSTHOG_KEY=...
VITE_POSTHOG_HOST=https://us.i.posthog.com
```

### 2.2 초기화 (`App.tsx`)
애플리케이션 진입점에서 `initAnalytics()`를 호출하여 SDK를 로드합니다.

---

## 3. 개발자 가이드

### 3.1 이벤트 전송 예시
직접 SDK를 호출하지 않고 `analytics` 객체의 메서드를 사용합니다.

```typescript
import { analytics } from '../services/analytics';

// 1. 페이지 조회
analytics.pageView('PracticePage');

// 2. 문제 선택 (상세 조회 시작)
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

// 4. 정답 제출 및 결과 (Core Action)
analytics.problemSubmitted(problemId, {
    isCorrect: true,
    difficulty: 'medium',
    dataType: 'pa'
});
```

### 3.2 디버깅 방법
1.  **브라우저 콘솔**: `analytics.setDebugMode(true)` 설정 시 전송되는 모든 이벤트가 콘솔에 로그로 출력됩니다. (관리자 계정은 자동 활성화)
2.  **Network 탭**: `api.mixpanel.com` 또는 `app.posthog.com`으로 나가는 페이로드를 직접 확인합니다.

---

## 4. 이벤트 사전 (Event Dictionary)

| 이벤트 명 | 발생 시점 | 용도 |
|:---|:---|:---|
| `Page Viewed` | 페이지 로드 시 | 트래픽 분석 |
| `Problem Viewed` | 문제 상세 진입 시 | 문제 도달률 측정 |
| `Problem Attempted` | 문제에서 첫 쿼리 실행/제출 시 | 풀이 시작율 측정 |
| `SQL Executed` | 실행 버튼 클릭 시 | SQL 복잡도 및 시도 횟수 분석 |
| `Problem Solved` ⭐ | 정답 판정 시 | **북극성 지표 (핵심 전환)** |
| `Hint Requested` | 힌트 버튼 클릭 시 | 문제 난이도 및 허들 분석 |

---

## 5. 분석 도구 바로가기
- **Mixpanel**: 실시간 이벤트 흐름 및 퍼널 분석
- **PostHog**: 사용자 세션 녹화 및 UI 인터랙션 확인

---

**모든 사용자 행동은 측정 가능해야 하며, 측정된 데이터는 제품 개선의 근거가 됩니다.**
