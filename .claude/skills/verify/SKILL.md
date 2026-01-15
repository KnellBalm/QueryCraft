---
name: verify
description: Run backend tests and frontend build/lint checks. Use when verifying code changes, before committing, or when user says "verify", "check", "테스트", "검증".
---

# Verify Project

프로젝트 전체 검증을 수행합니다 (CI와 동일한 검사).

## Instructions

1. **Backend Tests** 실행:
   ```bash
   export PYTHONPATH=$PYTHONPATH:$(pwd)
   pytest tests/test_grader.py tests/test_duckdb_engine.py -v
   ```

2. **Frontend Lint** 실행:
   ```bash
   cd frontend && npm run lint
   ```

3. **Frontend Build** 검증:
   ```bash
   cd frontend && npm run build
   ```

4. 결과 요약:
   - 성공한 항목과 실패한 항목을 명확히 보고
   - 실패 시 에러 내용과 수정 방향 제시

## Notes

- Backend 테스트는 PYTHONPATH 설정 필요
- Frontend 빌드는 TypeScript 타입 체크 포함 (`tsc -b && vite build`)
- 모든 검사 통과 시 커밋/PR 준비 완료
