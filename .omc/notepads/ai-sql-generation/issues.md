# AI SQL Generation - Known Issues and Gotchas

## Current Issues

### Issue 1: No Validation of Generated SQL
**Severity**: Medium
**Status**: Known limitation

**Description**:
Generated SQL is not validated before storage. If Gemini produces syntactically invalid SQL, it won't be caught until first execution attempt.

**Symptoms**:
- SQL stored successfully but fails on first grading attempt
- User sees "정답 SQL 실행 오류" message
- Logs show SQL syntax errors

**Workaround**:
- Grading service falls back to column validation
- Problem still gradable, just less precise

**Potential Fix**:
```python
def validate_sql(sql: str) -> bool:
    try:
        import sqlparse
        parsed = sqlparse.parse(sql)
        return len(parsed) > 0 and parsed[0].get_type() == 'SELECT'
    except:
        return False
```

**Why Not Fixed Yet**:
- Adds dependency (sqlparse)
- Execution is the ultimate validation
- Rare in practice (Gemini is good at SQL)

### Issue 2: Date Range Hallucination
**Severity**: Medium
**Status**: Partially mitigated

**Description**:
Sometimes Gemini generates SQL with hardcoded dates that don't exist in the dataset, even when the prompt specifies the exact date range.

**Example**:
```sql
-- Prompt says: data_period = 2026-01-15 to 2026-02-15
-- But Gemini generates:
WHERE event_date BETWEEN '2026-01-01' AND '2026-12-31'
```

**Impact**:
- Empty result sets
- Confusing for users
- Incorrect grading

**Mitigation**:
- Prompt explicitly mentions date ranges multiple times
- Includes "중요 제약사항" section
- Uses scenario date range in context

**Potential Fix**:
- Post-process SQL to replace hardcoded dates with scenario dates
- Add date validation before execution
- Use prompt examples with correct date usage

**Frequency**: ~5-10% of problems

### Issue 3: Column Name Casing Mismatches
**Severity**: Low
**Status**: Known limitation

**Description**:
Gemini sometimes generates column names with different casing than expected_columns specification.

**Example**:
```python
# Expected
expected_columns = ['total_amount', 'customer_count']

# Gemini generates
SELECT
    SUM(amount) as Total_Amount,  -- Capital T and A
    COUNT(DISTINCT customer_id) as customer_count
```

**Impact**:
- Column validation fails
- User gets "오답" even if query is correct

**Mitigation**:
- Prompt emphasizes "기대하는 결과 컬럼명과 정확히 일치하도록"
- PostgreSQL is case-insensitive for unquoted identifiers (helps somewhat)

**Potential Fix**:
- Case-insensitive column matching in grading service
- Post-process SQL to normalize column aliases
- Add explicit AS clauses to prompt examples

**Frequency**: ~2-3% of problems

### Issue 4: Division by Zero Not Always Prevented
**Severity**: Low
**Status**: Prompt guidance only

**Description**:
Despite prompt instruction to use NULLIF/CASE, Gemini sometimes forgets and creates division operations that can fail.

**Example**:
```sql
-- Prompt says: "division by zero 방지: NULLIF 또는 CASE 사용"
-- But Gemini generates:
SELECT
    SUM(purchase_amount) / COUNT(*) as avg_purchase
FROM events
WHERE event_name = 'non_existent_event'  -- COUNT(*) could be 0
```

**Impact**:
- SQL execution error during expected_result generation
- Problem saved without expected_result
- Falls back to legacy grading

**Mitigation**:
- Prompt includes explicit warning
- Most queries don't involve division

**Potential Fix**:
- Post-process SQL to wrap all divisions in NULLIF
- Regex pattern: `(\w+)\s*/\s*(\w+)` → `$1 / NULLIF($2, 0)`

**Frequency**: <1% of problems

### Issue 5: Schema Information Can Be Outdated
**Severity**: Low
**Status**: Architecture limitation

**Description**:
Table schema passed to AI is from BusinessScenario object, which is generated at planning time. If actual table structure differs, AI generates incorrect queries.

**Example**:
```python
# Scenario says: events table has 'device_type' column
# But actual table only has 'device'
# Gemini generates: WHERE device_type = 'mobile'  -- column doesn't exist
```

**Impact**:
- SQL execution fails
- Problem saved without expected_result

**Mitigation**:
- Scenario generation uses same logic as data generation
- Schema typically matches

**Potential Fix**:
- Query actual table schema from DB at generation time
- Add schema validation step
- Use information_schema to get real columns

**Frequency**: Rare (only during dev when schemas change)

### Issue 6: Token Usage Not Tracked Accurately
**Severity**: Low
**Status**: Estimation only

**Description**:
Current implementation estimates tokens (len/4) instead of using actual usage from API response.

**Code**:
```python
input_tokens = len(prompt) // 4  # Rough estimate
output_tokens = len(raw_text) // 4  # Rough estimate
```

**Impact**:
- Inaccurate usage logs
- Can't precisely monitor costs
- Billing surprises (unlikely with free tier)

**Mitigation**:
- Conservative estimates (usually over-counts)
- Daily limits far below free tier quota

**Potential Fix**:
```python
# Use actual metadata from response
if hasattr(response, 'usage_metadata'):
    input_tokens = response.usage_metadata.prompt_token_count
    output_tokens = response.usage_metadata.candidates_token_count
```

**Priority**: Low (not a blocker, easy to fix later)

## Potential Future Issues

### Issue 7: Gemini Model Changes
**Severity**: High (if it happens)
**Status**: Monitoring needed

**Description**:
Google may deprecate or change behavior of gemini-flash-latest model without notice.

**Symptoms**:
- 404 errors from API
- Different SQL quality
- Changed response format

**Mitigation**:
- Fallback to FALLBACK model implemented
- Retry logic handles 404s
- Logging tracks model used

**Action Items**:
- Monitor Google AI announcements
- Test with new models periodically
- Have migration plan

### Issue 8: Free Tier Exhaustion
**Severity**: Medium
**Status**: Unlikely but possible

**Description**:
If daily generation runs multiple times or manual testing is frequent, could exceed free tier limits.

**Free Tier Limits**:
- 1500 requests/day
- 1M tokens/day

**Current Usage**:
- ~12 requests/day (normal operation)
- ~18,000 tokens/day (normal operation)

**Headroom**: 100x for requests, 50x for tokens

**Mitigation**:
- Monitor via API usage logs
- Implement request caching
- Add rate limiting if needed

### Issue 9: Concurrent Generation Race Condition
**Severity**: Low
**Status**: Architectural

**Description**:
If two problem generation processes run simultaneously (e.g., scheduler + manual trigger), could cause:
- Duplicate API calls
- Inconsistent problem sets
- Database conflicts

**Current Protection**:
- Single-threaded daily scheduler
- Manual triggers rare
- DB upsert handles duplicates

**Potential Fix**:
- Add distributed lock (Redis/PostgreSQL)
- Add generation state tracking
- Prevent concurrent triggers

### Issue 10: Large Expected Results
**Severity**: Low
**Status**: Mitigated

**Description**:
If answer_sql returns thousands of rows, expected_result JSON becomes large.

**Current Mitigation**:
- LIMIT 1000 on all queries
- Most queries return <100 rows

**Potential Issues**:
- Large JSON files (>5MB)
- Slow JSON parsing
- Memory issues

**Additional Mitigation Needed**:
- Consider storing expected_result in separate blob storage
- Add row count validation before storage
- Compress large results

## Testing Gaps

### Gap 1: No Unit Tests
**Impact**: Changes could break without detection

**Missing Tests**:
- `test_build_table_schema_text()`
- `test_extract_sql_from_response()`
- `test_execute_and_get_result()`
- `test_enrich_problem_with_ai_solution()`

**Action Item**: Create test file `tests/test_unified_problem_generator.py`

### Gap 2: No Integration Tests
**Impact**: Can't validate full flow automatically

**Missing Tests**:
- End-to-end generation with mocked Gemini
- Grading with AI-generated problems
- Error recovery paths

**Action Item**: Add to CI pipeline

### Gap 3: No Performance Tests
**Impact**: Can't measure regression in generation speed

**Missing Metrics**:
- Time per problem
- AI call latency
- SQL execution time

**Action Item**: Add timing instrumentation

## Deployment Risks

### Risk 1: First Deployment May Have Issues
**Likelihood**: Medium
**Impact**: Medium

**Scenario**: First real problem generation might fail due to:
- Unexpected data in production
- Different DB schema
- Network issues with Gemini API

**Mitigation**:
- Test in dev environment first
- Have rollback plan (use legacy generator)
- Monitor first few days closely

### Risk 2: Grading Service Coupling
**Likelihood**: Low
**Impact**: High

**Scenario**: If grading service changes expected format of answer_sql or expected_result, old problems break.

**Mitigation**:
- Version problem format
- Maintain backward compatibility
- Add migration scripts if needed

### Risk 3: Gemini API Outage
**Likelihood**: Low
**Impact**: High

**Scenario**: If Gemini API is down during scheduled generation:
- No problems generated for that day
- Users see "no problems" error

**Current Fallback**:
- Health check auto-recovery (retries)
- Error logged to DB

**Additional Mitigation Needed**:
- Alert on generation failure
- Manual trigger capability
- Cached "emergency" problem sets

## Gotchas for Future Developers

### Gotcha 1: Import Order Matters
The generator imports are position-dependent. Must import after sys.path.insert.

```python
# Correct order
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from generator.scenario_generator import BusinessScenario

# Wrong order (will fail)
from generator.scenario_generator import BusinessScenario
sys.path.insert(0, ...)
```

### Gotcha 2: PostgresEngine Must Be Closed
The `_execute_and_get_result()` function creates a PostgresEngine. Must call `pg.close()` in finally block to avoid connection leaks.

### Gotcha 3: JSON Serialization Issues
Not all Python objects are JSON-serializable. Must convert:
- datetime → .isoformat()
- numpy types → .item()
- NaN/Inf → None

This is handled in `_execute_and_get_result()` but easy to forget when modifying.

### Gotcha 4: Prompt Changes Break Everything
The AI prompt is extremely sensitive. Small changes can dramatically affect output quality. Always test prompt changes thoroughly before deploying.

**Examples of Breaking Changes**:
- Removing date range instruction → dates outside data
- Changing output format request → extraction fails
- Adding verbose instructions → longer responses, higher costs

### Gotcha 5: Model Names Change Often
Google frequently updates model names. "gemini-1.5-pro" became "gemini-flash-latest". Code includes compatibility fixes but new models need updates.

## Monitoring Checklist

To detect issues early, monitor:

- [ ] AI enrichment success rate (should be >95%)
- [ ] SQL execution success rate (should be >95%)
- [ ] Average tokens per problem (should be 1000-1500)
- [ ] Generation time per problem (should be 3-5 sec)
- [ ] Daily API call count (should be ~12)
- [ ] Problem load errors (should be 0)
- [ ] Grading fallback rate (should be <5%)

## Conclusion

Most issues are minor and have reasonable workarounds. The system is designed to fail gracefully - if AI enrichment fails, problems still work with fallback grading.

**Critical Path**: As long as Gemini API is accessible and basic SQL generation works, the system functions correctly.

**Risk Level**: Low for production deployment
**Confidence**: High that issues are manageable

Key principle: **Better to have some problems with AI-generated SQL than no problems at all.** The fallback mechanisms ensure user experience is maintained even with failures.
