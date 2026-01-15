# 데이터 파이프라인 설계

## 1. Generator 모듈화 (서비스 운영/안정화)

### 현재 구조
```
backend/scheduler.py  # 모든 생성 로직이 하나의 파일에
```

### 개선 구조
```
backend/
├── generators/
│   ├── __init__.py
│   ├── base.py           # BaseGenerator 추상 클래스
│   ├── pa_generator.py   # PA 문제 생성
│   ├── rca_generator.py  # RCA 장애 시뮬
│   └── stream_generator.py
├── scheduler.py          # 스케줄러 (Generator 호출만)
└── services/
    └── generation_service.py  # 생성 서비스 레이어
```

### BaseGenerator 인터페이스
```python
class BaseGenerator(ABC):
    @abstractmethod
    def generate(self, date: str) -> GenerationResult: ...
    @abstractmethod
    def validate(self) -> bool: ...
    def log_result(self, result): ...
```

### 데이터 품질 검증 규칙

> ⚠️ 실무 수준의 데이터 품질을 위해 **논리적 일관성** 검증 필수

#### 이벤트 퍼널 규칙
```python
# 상위 이벤트 >= 하위 이벤트
assert page_views >= downloads
assert problem_viewed >= problem_attempted
assert problem_attempted >= problem_submitted
assert sessions >= unique_users
```

#### 시간 순서 규칙
```python
# 시작 < 종료
assert session_start < session_end
assert problem_started_at < problem_submitted_at
```

#### 수치 범위 규칙
```python
# 현실적인 범위
assert 0 < session_duration_seconds < 86400  # 최대 24시간
assert 0 < time_spent_minutes < 180  # 문제당 최대 3시간
assert 0 <= accuracy_rate <= 100
```

#### datetime 포맷 규칙
```python
# 초 단위까지만 (마이크로초 제외)
# ✅ 2026-01-16 00:30:45
# ❌ 2026-01-16T00:30:45.123456Z
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
```

#### DataValidator 클래스
```python
class DataValidator:
    def validate_funnel(self, data: dict) -> ValidationResult:
        """퍼널 순서 검증"""
        ...
    
    def validate_time_sequence(self, data: dict) -> ValidationResult:
        """시간 순서 검증"""
        ...
    
    def validate_ranges(self, data: dict) -> ValidationResult:
        """수치 범위 검증"""
        ...
```

### 현재 테이블
| 테이블 | 용도 |
|--------|------|
| `submissions` | 제출 기록 |
| `users` | 사용자 정보 |
| `system_logs` | 시스템 로그 |

### 활용 방안

#### A. 약점 분석 (이미 구현 시작됨)
- `stats_service.py` → `get_weakness_analysis()`
- 오답 패턴 → 맞춤 문제 추천

#### B. 운영 대시보드 확장
- 일별 활성 사용자(DAU)
- 문제별 정답률
- 평균 풀이 시간

---

## 3. Mixpanel 이벤트 분석

> 기존 `docs/archive/EVENT_DESIGN_GUIDELINE.md` 참조

### 핵심 퍼널
```
Page Viewed → Problem Viewed → Problem Attempted → Problem Submitted → Problem Solved
```

### 서비스 운영용 주요 이벤트

| 이벤트 | 속성 | 분석 목적 |
|--------|------|----------|
| `Problem Solved` | `difficulty`, `attempt_count`, `time_spent` | 문제 난이도 조정 |
| `Problem Failed` | `error_type`, `sql_snippet` | 오류 패턴 분석 |
| `Session Started` | `is_returning`, `last_visit_days` | 리텐션 분석 |
| `Feature Used` | `feature_name`, `track` | 기능별 사용량 |

### Mixpanel 대시보드 구성 (제안)

1. **Funnel Report**: 문제 풀이 퍼널 전환율
2. **Retention Report**: 주간/월간 재방문율
3. **Flow Report**: 사용자 탐색 경로
4. **Insights**: DAU, 문제 풀이 수, 정답률 추이

### AI 사용 임계치 분석

> 🎯 "사용자가 AI 도움 없이 얼마나 시도하는가?"

#### 수집 이벤트
| 이벤트 | 속성 | 설명 |
|--------|------|------|
| `Problem Started` | `problem_id`, `started_at` | 문제 시작 |
| `SQL Executed` | `attempt_number`, `is_correct` | 시도마다 트래킹 |
| `AI Help Requested` | `attempts_before`, `time_spent_before` | AI 도움 요청 시점 |
| `Problem Solved` | `total_attempts`, `used_ai` | 최종 해결 |

#### 분석 지표
```
1. 평균 시도 횟수 before AI:
   AVG(attempts_before) WHERE event = 'AI Help Requested'

2. 평균 체류 시간 before AI:
   AVG(time_spent_before) WHERE event = 'AI Help Requested'

3. AI 사용률 by 난이도:
   COUNT(used_ai=true) / COUNT(*) GROUP BY difficulty

4. 자력 해결 비율:
   COUNT(used_ai=false AND is_correct=true) / COUNT(*)
```

#### 인사이트 예시
- "사용자는 평균 3.2회 시도 후 AI 도움 요청"
- "5분 이상 고민 시 AI 사용 확률 80%"
- "Hard 문제는 1.5회만에 AI 요청, Easy는 5회"

---

## 4. Daily 문제 AI 도움 기능

### 요구사항
- **횟수 제한**: 문제당 1회만 사용 가능
- **도움 유형**: 사용자가 선택
  - 💡 힌트 (접근 방향 제시)
  - 📝 쿼리 작성 (정답 쿼리 제공)

### UI 구성
```
[AI 도움 받기 🤖] ← 1회 사용 가능
    ├─ 💡 힌트 받기
    └─ 📝 쿼리 작성해줘
```

### 이벤트 트래킹
| 이벤트 | 속성 |
|--------|------|
| `AI Help Requested` | `help_type`, `attempts_before`, `time_spent` |
| `AI Help Used` | `help_type`, `result_helpful` |

### 구현 파일
- `Workspace.tsx`: AI 도움 버튼 UI
- `api/sql.py`: AI 도움 엔드포인트
- `services/ai_helper.py`: Gemini API 호출

---

## 다음 단계

1. [ ] `generators/` 디렉토리 구조 생성
2. [ ] `BaseGenerator` 클래스 구현
3. [ ] Mixpanel 대시보드 설정
4. [ ] AI 사용 임계치 이벤트 트래킹 추가
5. [ ] Daily 문제 AI 도움 기능 구현
