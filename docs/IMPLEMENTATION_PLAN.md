# 문제 생성 스케줄링 및 날짜 오프셋 오류 수정 계획

KST 01:00에 실행되는 스케줄러가 UTC 날짜를 기준으로 문제를 생성함에 따라, 한국 사용자가 보는 시점에는 항상 전날 문제가 생성되는 문제를 해결합니다. 또한 Rule 7(오전 9시)과의 불일치를 해결하고 스케줄러 신뢰성을 높입니다.

### [Backend] 스케줄러 및 데이터 생성 로직 개선

#### [MODIFY] [scheduler.py](file:///home/naca11/QueryCraft/backend/scheduler.py)

- **타임존 명시**: `CronTrigger`에 `timezone='Asia/Seoul'`을 추가하고 실행 시간을 KST 기준으로 설정합니다.
- **날짜 계산 수정**: `date.today()` 대신 KST 기준 날짜를 사용하도록 `pytz` 등을 활용합니다.

#### [MODIFY] [data_generator_advanced.py](file:///home/naca11/QueryCraft/backend/generator/data_generator_advanced.py)

- **데이터 형식 변경**: 모든 `DATE` 타입 컬럼을 `TIMESTAMP`로 변경하고, 데이터 생성 시 `YYYY-MM-DD HH:MM:SS` 형식의 문자열 또는 타임존 없는 `datetime` 객체를 사용합니다.
- **포스트그레스 공지**: DB 연결 실패나 엔진 확인 부분에 PostgreSQL 전용임을 알리는 로깅 또는 예외 메시지를 추가합니다.

#### [MODIFY] [problem_service.py](file:///home/naca11/QueryCraft/backend/services/problem_service.py)

- **JSONB 파싱 버그 수정**: PostgreSQL `jsonb` 데이터가 이미 `dict`로 로드되는 경우 `json.loads` 시 발생하는 `TypeError`를 해결했습니다.
- **세트 인덱스 폴백**: 특정 세트 인덱스(0, 1 외)를 가진 사용자에게도 오늘 생성된 문제가 있으면 제공되도록 폴백을 강화했습니다.

### [Frontend] 사용자 안내 추가

#### [MODIFY] [Workspace.tsx](file:///home/naca11/QueryCraft/frontend/src/pages/Workspace.tsx) 및 [App.tsx](file:///home/naca11/QueryCraft/frontend/src/App.tsx)

- UI 상단 혹은 헬프 텍스트에 "현재 QueryCraft는 PostgreSQL 문법만을 지원합니다"라는 안내 문구를 추가합니다.

---

## Verification Plan

### Automated Tests
- `scripts/manual_trigger.py` 실행 후 생성된 데이터의 형식이 `YYYY-MM-DD HH:MM:SS`인지 SQL 쿼리로 확인합니다.
- (예: `SELECT signup_at FROM pa_users LIMIT 1;`)

### Manual Verification
1. **Frontend UI 확인**: 워크스페이스 및 메인 화면에 PostgreSQL 지원 안내가 노출되는지 확인합니다.
2. **스케줄러 상태 확인**: `GET /admin/scheduler-status`에서 타임존이 `Asia/Seoul`로 표시되는지 확인합니다.

> [!IMPORTANT]
> 상용 서버 적용 시에는 `docker compose restart backend`를 통해 변경된 로직을 즉시 반영해야 합니다.
