# DailyChallenge 'date' undefined 에러 해결 계획

## 문제 원인
1. **백엔드 DB 엔진 미흡**: `PostgresEngine`에 `fetch_one` 메소드가 없어 DB에서 Daily Challenge를 로드하는 데 실패합니다.
2. **데이터 포맷 불일치**: DB 로드 실패 시 파일 시스템(`problems/daily/`)에서 데이터를 로드하는데, 일부 파일이 최신 통합 포맷(v2.0, Object)이 아닌 이전 포맷(List)으로 되어 있어 프론트엔드에서 `challenge.scenario`가 `undefined`가 됩니다.
3. **성적 데이터 불일치**: `stats_service.py`가 `users` 테이블에 저장된 `xp`/`level`을 사용하지 않고 `submissions` 테이블에서 실시간 계산을 수행하며, 이 과정에서 관리자 페이지(DB 직접 조회)와 다른 결과가 표시됩니다.
4. **결정적 버그 (NameError)**: `stats_service.py` 내부에 `import pandas as pd`가 누락되어 있어, `pd.notnull` 호출 시 에러가 발생하고 통계 정보가 0으로 초기화됩니다.

## 제안된 변경 사항

### [Backend] Database Engine & Service
#### [MODIFY] [postgres_engine.py](file:///Users/zokr/python_workspace/QueryCraft/backend/engine/postgres_engine.py)
- `fetch_one`, `fetch_all` 메소드 추가 (psycopg2를 사용하여 Dict 형태의 결과 반환)
- 일관성을 위해 `DuckDBEngine`의 메소드 명명 규칙과 맞추거나 별칭 제공

#### [MODIFY] [daily_challenge_writer.py](file:///Users/zokr/python_workspace/QueryCraft/backend/generator/daily_challenge_writer.py)
- `load_daily_challenge` 및 `get_latest_challenge`에서 로드된 데이터가 리스트(v1.0)인 경우, v2.0 형식으로 자동 변환하는 로직 추가

#### [MODIFY] [stats_service.py](file:///Users/zokr/python_workspace/QueryCraft/backend/services/stats_service.py)
- `import pandas as pd` 추가
- `get_user_stats` 및 `get_level`에서 `submissions` 테이블 실시간 계산 대신 `public.users` 테이블에 저장된 `xp`, `level` 값을 우선적으로 사용하도록 수정
- 레벨 체계를 `grading_service.py`와 동일하게 `xp / 100 + 1` 기반으로 통일하거나, 저장된 값을 그대로 노출

### [Frontend] UI Robustness
#### [MODIFY] [DailyChallenge.tsx](file:///Users/zokr/python_workspace/QueryCraft/frontend/src/pages/DailyChallenge.tsx)
- `challenge.scenario` 접근 전 방어 코드 추가 (Optional chaining 사용 등)
- 데이터가 유효하지 않을 경우의 에러 메시지 개선

## 검증 계획

### 자동 테스트
- `backend/tests/test_daily_challenge.py` (신규 생성) 를 통해 DB 로딩 및 포맷 변환 로직 검증

### 수동 검증
- 웹 브라우저를 통해 `/daily/latest` 페이지가 정상적으로 렌더링되는지 확인 (에러 로그 발생 여부 체크)
