# Walkthrough: Problem Generation Schedule & Data Format Fix

상용 서버에서 발생한 문제 생성 지연 이슈를 해결하고, 데이터 형식을 사용자 요구사항(`YYYY-MM-DD HH:MM:SS`)에 맞게 표준화했습니다.

## 주요 변경 사항

### 1. KST 기반 스케줄링 및 날짜 계산 오류 수정
- **문제**: 스케줄러가 UTC 기준으로 작동하여 한국 시간(KST) 새벽 1시 실행 시 날짜가 계산되는 시점이 전날로 인식되는 오프셋이 발생했습니다.
- **해결**: `backend/scheduler.py`의 `CronTrigger`에 `timezone='Asia/Seoul'`을 명시하고, `datetime.now(kst)`를 사용하여 날짜를 명확히 계산하도록 수정했습니다.

### 2. 데이터 형식 표준화 (`YYYY-MM-DD HH:MM:SS`)
- **문제**: 기존 데이터가 `DATE` 타입(YYYY-MM-DD)으로 저장되거나 타임존 정보가 포함되어 있었습니다.
- **해결**:
    - `pa_users`, `pa_sessions`, `pa_events` 등 주요 테이블의 스키마를 `TIMESTAMP`로 변경(동기화)했습니다.
    - 데이터 생성 시 `strftime("%Y-%m-%d %H:%M:%S")`를 사용하여 타임존 없는 문자열 형식을 보장했습니다.
    - 모든 데이터에 랜덤한 시/분/초를 부여하여 데이터의 생동감을 높였습니다.

### 3. PostgreSQL 전용 지원 안내 및 AI 프롬프트 개선
- **문제**: PostgreSQL에서 `round(double precision, int)` 함수가 존재하지 않아 발생하는 오류를 방지해야 했습니다.
- **해결**: 
    - AI 프롬프트(`problems/prompt_pa.py`, `problems/generator_stream.py`)를 수정하여 `ROUND(column::numeric, 2)`와 같이 명시적인 타입 캐스팅을 사용하도록 가이드를 강화했습니다.
    - 프론트엔드(`MainPage.tsx`, `Workspace.tsx`)에 "PostgreSQL 전용" 안내 문구를 추가하여 사용자 혼란을 방지했습니다.

### 4. JSONB 파싱 버그 수정 (추가 발견)
- **문제**: PostgreSQL의 `jsonb` 컬럼이 `pandas`를 통해 로드될 때 자동으로 Python `dict`로 변환되고 있었으나, 코드에서 `json.loads()`를 중복 호출하여 `TypeError`가 발생, 결과적으로 DB에서 문제를 불러오지 못하고 있었습니다.
- **해결**: `backend/services/problem_service.py`에서 데이터 타입을 확인하여 `dict`인 경우 파징을 건너뛰도록 수정했습니다. 또한 특정 `set_index`를 가진 사용자에게도 오늘 생성된 문제가 있으면 제공되도록 폴백 로직을 강화했습니다.

## 검증 결과

### 데이터 형식 확인
`scripts/check_schema.py` 및 수동 쿼리를 통해 데이터 형식이 변경되었음을 확인했습니다.

```bash
# pa_users 데이터 확인 결과
            signup_at
0 2025-11-14 10:31:42
1 2025-11-14 10:31:42
...
```

### 정답 SQL 구문 확인
생성된 문제들의 `answer_sql`에서 `::numeric` 캐스팅이 올바르게 적용되었습니다.

```sql
-- 개선된 정답 SQL 예시
ROUND(CAST(engagement_events_count AS NUMERIC) / view_feed_count, 4)
ROUND((ec.user_count::numeric / fs.user_count), 2)
```

## 상용 서버 배포 가이드

변경된 내용을 상용 서버에 반영하려면 다음 명령어를 실행하십시오:

```bash
# 백엔드 컨테이너 재시작 (스케줄러 및 로직 반영)
docker compose restart backend

# 프론트엔드 빌드 및 배포
docker compose build frontend && docker compose up -d frontend
```

> [!NOTE]
> 스케줄러는 이제 매일 KST 새벽 1시에 정확한 날짜의 문제를 생성합니다.
