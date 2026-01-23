# 버그 수정 및 안정성 강화 (2026-01-20)

## 배경 및 목표
상용 서버 배포 후 보고된 404 에러, 에디터 스타일 충돌, 문제 세트 필터링 오류, 스트릭 계산 버그를 해결하여 시스템을 안정화함.

## 해결된 이슈 및 변경 사항

### 1. 404 Not Found 에러 및 로깅 강화
- **OAuth 콜백**: `auth.py`에서 누락된 `/api` prefix 추가.
- **로깅**: `main.py`에 404 URL 상세 로깅 미들웨어 추가.
- **프론트엔드**: `Workspace.tsx`에서 잘못된 `dataType` 요청 차단.

### 2. 에디터 자동 완성 가시성 및 스타일 충돌 해결
- **전역 스타일 분리**: `App.css`의 `.main` 클래스를 `.app-main`으로 변경하여 Monaco 에디터 내부 클래스와의 충돌(height: 0px) 해결.
- **에디터 색상**: `Workspace.css`에서 자동 완성 위젯의 텍스트 색상 및 하이라이트 강제 지정.

### 3. 문제 세트 필터링 (12개 -> 사용자별 6개)
- **생성기**: `unified_problem_generator.py`가 하루 2세트(12문제)를 생성하도록 확장.
- **API**: `daily.py`에서 `user_id` 기반 `set_index` 필터링 로직 구현.
- **데이터**: 2026-01-20일자 데이터를 12문제 버전으로 재생성.

### 4. 연속 일수(Streak) 로직 개선
- **계산 방식**: `stats_service.py`에서 오늘 아직 제출이 없더라도 어제의 제출 기록이 있으면 스트릭을 유지하도록 수정.

### 5. CORS 및 404 에러 해결 (PathRewriteMiddleware)
- **증상**: 프론트엔드에서 `/auth/me` 등 `/api` 접두사가 누락된 요청을 보낼 때 404가 발생하고, 이로 인해 CORS 오류로 오인됨.
- **해결**: `backend/common/middleware.py`에 `PathRewriteMiddleware` 구현.
- **적용**: `main.py`에 미들웨어 등록 (CORS 이전에 실행되도록 배치하여 경로 수정 후 CORS 헤더 적용).
- **테스트**: `tests/test_middleware.py` 추가하여 경로 재작성 로직 검증 완료.

## 검증 계획
- [x] 백엔드 유닛 테스트: `pytest` (환경 구축 필요 시 스킵 가능)
- [x] 프론트엔드 빌드 체크: `npm run build`
- [x] 로컬 통합 테스트: `daily_challenge_writer.py`를 통한 데이터 로드 확인
