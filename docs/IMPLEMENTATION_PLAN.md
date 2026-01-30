# AI API 키 동기화 및 서비스 복구 계획

새로 발급받은 유효한 Gemini API 키를 시스템 전체(로컬 및 클라우드)에 동기화하여 AI 도움, 문제 생성, 오늘의 팁 등 모든 AI 기능을 복구했습니다. 또한 로그에서 발견된 인자 오류를 함께 수정했습니다.

## 변경 사항

### 로컬 환경 설정
- **[.env](file:///Users/zokr/python_workspace/QueryCraft/.env)**: `GEMINI_API_KEY` 업데이트 완료.
- **[.env.dev](file:///Users/zokr/python_workspace/QueryCraft/.env.dev)**: `GEMINI_API_KEY` 업데이트 완료.

### Cloud Run 서비스 업데이트
- **`query-craft-backend`**: `GEMINI_API_KEY` 업데이트 완료 (사용자 실행).
- **`tip-worker`**: `GEMINI_API_KEY` 업데이트 완료.
- **`problem-worker`**: `GEMINI_API_KEY` 업데이트 완료.

### 코드 수정
- **[unified_problem_generator.py](file:///Users/zokr/python_workspace/QueryCraft/backend/generator/unified_problem_generator.py)**: `generate_pa_problem` 및 `generate_stream_problem`의 `_problem_number` 인자명을 `problem_number`로 수정하여 `unexpected keyword argument` 에러 해결.

## 검증 결과
- `test_gemini.py`를 통한 API 호출 성공 확인.
- Cloud Run 서비스 배포 성공 확인.
