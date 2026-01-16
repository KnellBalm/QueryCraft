# Generator 모듈 가이드

QueryCraft의 데이터 및 문제 생성기 모듈입니다.

## 📁 디렉토리 구조

```
backend/generator/
├── __init__.py
├── base.py                     # BaseGenerator 추상 클래스
├── validator.py                # DataValidator 검증 클래스
├── example_generator.py        # 사용 예시
├── data_generator_advanced.py  # 실제 데이터 생성 로직
├── anomaly_injector.py         # RCA 이상 주입
├── config.py                   # 생성 설정
├── product_config.py           # 제품 프로필
└── utils.py                    # 유틸리티 함수
```

---

## 🏗️ BaseGenerator 추상 클래스

모든 Generator는 `BaseGenerator`를 상속받아 구현합니다.

### 기본 구조

```python
from backend.generator.base import BaseGenerator, GenerationResult

class MyGenerator(BaseGenerator):
    def __init__(self):
        super().__init__("MyGenerator")
        # 초기화 로직

    def generate(self, target_date: str) -> GenerationResult:
        """실제 생성 로직"""
        # 데이터/문제 생성
        return GenerationResult(
            success=True,
            data=generated_data
        )

    def validate(self) -> bool:
        """검증 로직"""
        # 생성된 데이터 검증
        return True
```

### 제공되는 메서드

#### `run(date: str) -> GenerationResult`
- **용도**: 생성 실행 (래퍼 메서드)
- **기능**:
  - 시간 측정
  - 자동 로깅
  - 예외 처리
- **사용**:
  ```python
  generator = MyGenerator()
  result = generator.run("2026-01-16")
  ```

#### `log_result(result: GenerationResult)`
- **용도**: 결과를 DB 로그에 기록
- **기능**:
  - 성공/실패 로깅
  - LogCategory.GENERATOR 카테고리로 저장
- **사용**:
  ```python
  generator.log_result(result)
  ```

---

## 🔍 DataValidator 검증 클래스

생성된 데이터의 논리적 일관성을 검증합니다.

### 검증 규칙

#### 1. 퍼널 검증 (`validate_funnel`)
상위 이벤트 >= 하위 이벤트

```python
from backend.generator.validator import DataValidator

validator = DataValidator()
data = {
    "page_views": 1000,
    "downloads": 500,
    "signups": 250
}

result = validator.validate_funnel(data, [
    ("page_views", "downloads"),
    ("downloads", "signups")
])

if result.is_valid:
    print("✓ 퍼널 검증 통과")
else:
    print(f"✗ 퍼널 위반: {result.errors}")
```

#### 2. 시간 순서 검증 (`validate_time_sequence`)
시작 < 종료

```python
data = {
    "session_start": "2026-01-16 10:00:00",
    "session_end": "2026-01-16 11:00:00"
}

result = validator.validate_time_sequence(data, [
    ("session_start", "session_end")
])
```

#### 3. 수치 범위 검증 (`validate_ranges`)
현실적인 범위 내 값

```python
data = {
    "session_duration": 3600,
    "accuracy_rate": 85.5
}

result = validator.validate_ranges(data, {
    "session_duration": (0, 86400),  # 0~24시간
    "accuracy_rate": (0, 100)
})
```

#### 4. datetime 포맷 검증 (`validate_datetime_format`)
YYYY-MM-DD HH:MM:SS 형식

```python
data = {
    "created_at": "2026-01-16 10:30:45"
}

result = validator.validate_datetime_format(data, ["created_at"])
```

#### 5. 통합 검증 (`validate_all`)
모든 규칙을 한번에 검증

```python
result = validator.validate_all(
    data,
    funnel_rules=[("page_views", "downloads")],
    time_rules=[("session_start", "session_end")],
    range_rules={"session_duration": (0, 86400)},
    datetime_keys=["created_at"]
)
```

---

## 📝 실전 예시

### 1. 간단한 Generator 구현

```python
from backend.generator.base import BaseGenerator, GenerationResult
from backend.generator.validator import DataValidator

class DailyStatsGenerator(BaseGenerator):
    def __init__(self):
        super().__init__("DailyStatsGenerator")
        self.validator = DataValidator()
        self.stats = None

    def generate(self, target_date: str) -> GenerationResult:
        """일일 통계 생성"""
        try:
            # 1. 통계 계산
            self.stats = {
                "date": target_date,
                "active_users": 5000,
                "sessions": 8000,
                "page_views": 15000
            }

            # 2. 검증
            if not self.validate():
                return GenerationResult(
                    success=False,
                    error="Validation failed"
                )

            # 3. 성공
            return GenerationResult(
                success=True,
                data=self.stats,
                metadata={"date": target_date}
            )

        except Exception as e:
            return GenerationResult(
                success=False,
                error=str(e)
            )

    def validate(self) -> bool:
        """검증: sessions >= active_users"""
        result = self.validator.validate_funnel(
            self.stats,
            [("sessions", "active_users")]
        )
        return result.is_valid

# 사용
generator = DailyStatsGenerator()
result = generator.run("2026-01-16")

if result.success:
    print(f"✓ 생성 완료: {result.data}")
    print(f"  소요 시간: {result.duration_seconds:.2f}초")
else:
    print(f"✗ 실패: {result.error}")
```

### 2. 일괄 생성

```python
from datetime import date, timedelta

generator = DailyStatsGenerator()
start_date = date(2026, 1, 1)

for i in range(7):  # 일주일치
    target = (start_date + timedelta(days=i)).isoformat()
    result = generator.run(target)

    if result.success:
        print(f"✓ {target}: OK ({result.duration_seconds:.2f}s)")
        generator.log_result(result)  # DB 로깅
    else:
        print(f"✗ {target}: {result.error}")
```

### 3. 고급 검증

```python
class ProblemGenerator(BaseGenerator):
    def validate(self) -> bool:
        """다중 규칙 검증"""
        if not self.problem_data:
            return False

        # 통합 검증
        result = self.validator.validate_all(
            self.problem_data,
            funnel_rules=[
                ("problem_viewed", "problem_attempted"),
                ("problem_attempted", "problem_submitted"),
                ("problem_submitted", "problem_solved")
            ],
            time_rules=[
                ("started_at", "submitted_at")
            ],
            range_rules={
                "time_spent_minutes": (0, 180),  # 최대 3시간
                "attempt_count": (1, 100)
            },
            datetime_keys=["started_at", "submitted_at"]
        )

        if not result.is_valid:
            logger.error(f"Validation failed: {result.errors}")
            return False

        if result.warnings:
            logger.warning(f"Validation warnings: {result.warnings}")

        return True
```

---

## 🧪 테스트

### 단위 테스트

```bash
# Validator 테스트
pytest tests/test_validator.py -v

# 특정 테스트 실행
pytest tests/test_validator.py::TestDataValidator::test_validate_funnel_success -v
```

### 통합 테스트

```python
def test_generator_integration():
    """Generator 통합 테스트"""
    generator = MyGenerator()

    # 1. 생성 실행
    result = generator.run("2026-01-16")
    assert result.success is True

    # 2. 데이터 검증
    assert result.data is not None
    assert result.duration_seconds > 0

    # 3. 결과 로깅
    generator.log_result(result)

    # 4. 마지막 결과 확인
    assert generator.last_result.success is True
```

---

## 📊 GenerationResult 데이터 구조

```python
@dataclass
class GenerationResult:
    success: bool                     # 성공 여부
    data: Optional[Any] = None        # 생성된 데이터
    error: Optional[str] = None       # 에러 메시지
    duration_seconds: float = 0.0     # 소요 시간 (초)
    metadata: Optional[dict] = None   # 추가 메타데이터

    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        ...
```

---

## 📊 ValidationResult 데이터 구조

```python
@dataclass
class ValidationResult:
    is_valid: bool          # 검증 성공 여부
    errors: List[str]       # 에러 목록
    warnings: List[str]     # 경고 목록

    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        ...
```

---

## 🔧 설정

### config.py
생성기 전역 설정 (시드, 규모, 확률 등)

```python
# 생성 규모
PA_NUM_USERS = 50000
STREAM_N_USERS = 50000

# 시드 모드
GEN_SEED_MODE = "date"  # "date" | "fixed" | "none"
GEN_SEED_FIXED = 12345
```

### product_config.py
제품 프로필별 설정 (이커머스, SaaS, 콘텐츠 등)

---

## 🚀 베스트 프랙티스

1. **항상 BaseGenerator 상속**
   - 표준화된 인터페이스 사용
   - 시간 측정, 로깅 자동 처리

2. **검증 필수**
   - 퍼널 규칙, 시간 순서, 수치 범위 검증
   - DataValidator 활용

3. **예외 처리**
   - generate() 내부에서 try-except
   - GenerationResult로 에러 반환

4. **로깅 활용**
   - run() 메서드가 자동 로깅
   - log_result()로 DB 로그 기록

5. **테스트 작성**
   - 단위 테스트 (pytest)
   - 검증 로직 테스트
   - 통합 테스트

---

## 📚 참고 문서

- `example_generator.py` - 상세한 구현 예시
- `tests/test_validator.py` - 검증 테스트 예시 (35개 테스트)
- `docs/IMPLEMENTATION_PLAN.md` - 아키텍처 설계 문서
