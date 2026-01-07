# QueryCraft MSA 아키텍처 및 멀티모델 Gemini 구현 계획

## 1. 아키텍처 개요

### 현재 구조 (모놀리식)
```
┌─────────────────────────────────────────┐
│          Cloud Run (Backend)            │
│  ┌────────────────────────────────────┐ │
│  │ 쿼리 에디터 + 문제 생성 + 채점     │ │
│  │ + 스케줄러 + 데이터 생성           │ │
│  └────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

### 개선 구조 (MSA)
```
┌──────────────────────┐     ┌──────────────────────┐
│  Cloud Run (API)     │     │ Cloud Functions      │
│  ┌────────────────┐  │     │  (Problem Worker)    │
│  │ 쿼리 에디터    │  │     │  ┌────────────────┐  │
│  │ 사용자 API     │  │     │  │ 문제 생성      │  │
│  │ 채점 (조회)    │  │     │  │ 데이터 생성    │  │
│  └────────────────┘  │     │  │ 채점 정답 생성 │  │
└──────────────────────┘     └──────────────────────┘
         │                            │
         └──────────┬─────────────────┘
                    ▼
            ┌──────────────┐
            │   Supabase   │
            │  (PostgreSQL)│
            └──────────────┘
```

## 2. 서비스 분리

### Service A: Query API (Cloud Run)
**역할:** 사용자 요청 처리, 실시간 응답 필요
- `/auth/*` - 인증
- `/problems/*` - 문제 조회 (DB에서)
- `/sql/*` - SQL 실행/제출
- `/stats/*` - 통계/리더보드
- `/admin/*` - 관리자 (트리거만)

**특징:**
- 빠른 응답 (< 100ms)
- Stateless
- Auto-scaling (0-2 인스턴스)

### Service B: Problem Worker (Cloud Functions)
**역할:** 무거운 AI 작업, 비동기 처리
- 문제 생성 (Gemini API)
- 데이터셋 생성
- 채점 정답 테이블 생성
- 오늘의 팁 생성

**특징:**
- 긴 실행 시간 허용 (최대 9분)
- 스케줄러 트리거
- 독립적인 장애 격리

## 3. Gemini 멀티모델 전략

### 모델 배분표

| 용도 | 모델 | 이유 |
|------|------|------|
| **문제 생성** | `gemini-2.5-flash` | 데이터 분석 + 창의적 문제 필요, 품질 중요 |
| **채점 SQL 검증** | `gemini-2.5-flash` | 정확한 SQL 분석 필요 |
| **오늘의 팁** | `gemini-2.5-flash-lite` | 간단한 텍스트 생성, 경량으로 충분 |
| **힌트 생성** | `gemini-2.5-flash-lite` | 짧은 응답, 빠른 속도 |
| **에러 설명** | `gemini-3-flash` | 최신 모델로 정확한 설명 |

### 구현 코드

```python
# problems/gemini.py
import os
from google import genai

class GeminiModels:
    """용도별 Gemini 모델 관리"""
    
    # 모델 정의
    PROBLEM_GENERATION = os.getenv("GEMINI_MODEL_PROBLEM", "gemini-2.5-flash")
    GRADING = os.getenv("GEMINI_MODEL_GRADING", "gemini-2.5-flash")
    TIPS = os.getenv("GEMINI_MODEL_TIPS", "gemini-2.5-flash-lite")
    HINTS = os.getenv("GEMINI_MODEL_HINTS", "gemini-2.5-flash-lite")
    ERROR_EXPLAIN = os.getenv("GEMINI_MODEL_ERROR", "gemini-3-flash")
    
    @classmethod
    def get_client(cls, purpose: str):
        """용도에 맞는 모델로 클라이언트 생성"""
        model_map = {
            "problem": cls.PROBLEM_GENERATION,
            "grading": cls.GRADING,
            "tips": cls.TIPS,
            "hints": cls.HINTS,
            "error": cls.ERROR_EXPLAIN,
        }
        model = model_map.get(purpose, cls.TIPS)
        return genai.Client(api_key=os.getenv("GEMINI_API_KEY")), model
```

### 할당량 분산 효과

```
무료 티어 (일일 한도 예상):
┌─────────────────────────┬──────────────────┐
│ gemini-2.5-flash        │ 1,500 req/day    │
│ gemini-2.5-flash-lite   │ 3,000 req/day    │
│ gemini-3-flash          │ 1,500 req/day    │
├─────────────────────────┼──────────────────┤
│ 총 가용량               │ 6,000 req/day    │
└─────────────────────────┴──────────────────┘
```

## 4. 데이터 구조 변경

### 새로운 Supabase 테이블

```sql
-- 문제 저장 (파일 → DB)
CREATE TABLE problems (
    id SERIAL PRIMARY KEY,
    problem_date DATE NOT NULL,
    data_type VARCHAR(20) NOT NULL,  -- 'pa', 'stream'
    set_index INTEGER DEFAULT 0,
    difficulty VARCHAR(20),
    title TEXT NOT NULL,
    description TEXT,
    initial_sql TEXT,
    expected_answer JSONB,
    hints JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(problem_date, data_type, set_index, title)
);

-- 오늘의 팁
CREATE TABLE daily_tips (
    id SERIAL PRIMARY KEY,
    tip_date DATE UNIQUE NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 워커 실행 로그
CREATE TABLE worker_logs (
    id SERIAL PRIMARY KEY,
    job_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    model_used VARCHAR(50),
    tokens_used INTEGER,
    duration_ms INTEGER,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## 5. Cloud Functions 구현

### 디렉토리 구조
```
QueryCraft/
├── backend/              # Service A (Cloud Run)
│   ├── api/
│   ├── services/
│   └── main.py
│
├── functions/            # Service B (Cloud Functions)
│   ├── problem_worker/
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   └── generator/
│   ├── tip_worker/
│   │   ├── main.py
│   │   └── requirements.txt
│   └── deploy.sh
│
├── shared/               # 공통 코드
│   ├── gemini_models.py
│   ├── supabase_client.py
│   └── schemas.py
```

### Problem Worker (Cloud Function)

```python
# functions/problem_worker/main.py
import functions_framework
from datetime import date
from shared.gemini_models import GeminiModels
from shared.supabase_client import get_supabase

@functions_framework.http
def generate_problems(request):
    """매일 KST 01:00에 Cloud Scheduler가 호출"""
    today = date.today()
    client, model = GeminiModels.get_client("problem")
    supabase = get_supabase()
    
    try:
        # 1. 데이터 요약 생성
        # 2. Gemini로 문제 생성
        # 3. Supabase에 저장
        # 4. 로그 기록
        
        return {"success": True, "count": problem_count}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

## 6. 배포 전략

### Phase 1: 현재 유지 + 최적화 (이번 주)
1. [x] Gemini 모델 변경 (`gemini-1.5-flash`)
2. [ ] 배포 시 자동 생성 제거
3. [ ] `problems` 테이블 생성
4. [ ] 문제 조회를 파일 → DB로 변경

### Phase 2: 워커 분리 (다음 주)
1. [ ] Cloud Functions 프로젝트 생성
2. [ ] `problem_worker` 구현
3. [ ] Cloud Scheduler 설정 (KST 01:00)
4. [ ] 테스트 및 안정화

### Phase 3: 멀티모델 적용 (2주차)
1. [ ] `GeminiModels` 클래스 구현
2. [ ] 용도별 모델 분리
3. [ ] 할당량 모니터링 대시보드
4. [ ] 폴백 로직 추가

## 7. 예상 비용

| 서비스 | 무료 티어 | 예상 사용량 | 비용 |
|--------|-----------|-------------|------|
| Cloud Run (API) | 2M req/월 | ~10K req/월 | $0 |
| Cloud Functions | 2M req/월 | ~100 req/월 | $0 |
| Cloud Scheduler | 3 jobs/월 | 3 jobs/월 | $0 |
| Gemini API | 위 참조 | 분산 사용 | $0 |
| Supabase | 500MB | ~50MB | $0 |

**총 예상 비용: $0/월** (무료 티어 내 운영)

## 8. 다음 단계

관리자님의 승인 시:
1. `problems` 테이블 스키마 적용
2. 배포 시 자동 생성 제거
3. 문제 조회 API를 DB 기반으로 변경
4. `GeminiModels` 클래스 구현

진행할까요?
