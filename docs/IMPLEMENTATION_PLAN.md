# Harmonize Problem Loading and Fix Submission Error

This plan addresses the "Problem Not Found" error that occurs when submitting SQL for a problem that exists in the database but is missing from the local filesystem. It also improves error reporting by using proper HTTP status codes.

## Proposed Changes

### [Backend] Problem Retrieval Harmonization

#### [MODIFY] [grading_service.py](file:///mnt/z/GitHub/QueryCraft/backend/services/grading_service.py)
- Replace internal `load_problem` function with a call to `problem_service.get_problem_by_id`.
- This ensures that problems found in the DB are also available for grading.
- Update `grade_submission` to handle the `Problem` object (Pydantic model) instead of a raw dictionary.

### [Backend] API Error Handling Improvement

#### [MODIFY] [sql.py](file:///mnt/z/GitHub/QueryCraft/backend/api/sql.py)
- Update `submit_answer` to check if the submission grading returned a "Problem Not Found" state.
- Raise `HTTPException(404, "문제를 찾을 수 없습니다.")` if the problem cannot be retrieved.

## Verification Plan

### Automated Verification
- Run a manual submission test through the UI.
- Verify that `is_fetching` state is properly handled (already handled by previous fix).
- Check backend logs for `[INFO] Problem found: ...` vs `[ERROR] Problem not found: ...`.

### Manual Verification
- **Scenario 1**: Problem exists in both file and DB. (Verify submission success)
- **Scenario 2**: Problem exists only in DB. (Verify submission success - this was failing before)
- **Scenario 3**: Problem exists in neither. (Verify 404 response)
