# AI SQL Generation Implementation - Learnings

## Overview
Successfully implemented AI-powered SQL generation for the unified problem generator. This adds `answer_sql` and `expected_result` fields to all generated problems.

## Key Components Added

### 1. `enrich_problem_with_ai_solution(problem, scenario)`
Main function that enriches a problem with AI-generated SQL solution.

**Location**: `backend/generator/unified_problem_generator.py:78-126`

**Flow**:
1. Builds table schema text from scenario
2. Constructs detailed prompt for Gemini
3. Calls Gemini 2.0 Flash to generate SQL
4. Extracts SQL from response (handles code blocks)
5. Executes SQL to generate expected_result
6. Returns enriched problem dict

**Error Handling**:
- If AI generation fails: logs warning, returns original problem (allows fallback grading)
- If SQL execution fails: logs error, stores answer_sql but leaves expected_result empty

### 2. Helper Functions

#### `_build_table_schema_text(scenario)`
Converts scenario's TableConfig objects into readable text format for AI context.

**Output Format**:
```
## 사용 가능한 테이블

### warehouse.events_20260128
목적: 사용자 행동 이벤트
행 수: 50,000개
컬럼:
  - event_id (TEXT, NOT NULL)
  - user_id (TEXT, NOT NULL)
  - event_time (TIMESTAMP, NOT NULL)
  ...
```

#### `_build_sql_generation_prompt(problem, scenario, table_schema)`
Constructs comprehensive prompt for Gemini including:
- Business background (company, situation, industry)
- Problem details (question, difficulty, topic, requester)
- Expected result columns
- Table schema information
- Important constraints (PostgreSQL syntax, date ranges, no division by zero)

**Critical Constraints in Prompt**:
1. PostgreSQL syntax only
2. Use only specified tables/columns
3. Prevent division by zero with NULLIF/CASE
4. Date conditions must be within data_period range
5. Match expected column names exactly
6. No semicolons, no comments

#### `_extract_sql_from_response(response_text)`
Robust SQL extraction from Gemini responses:
1. First tries to extract from code blocks (```sql or ```)
2. Falls back to treating entire response as SQL
3. Removes comments (-- and /* */)
4. Strips semicolons and whitespace
5. Validates minimum length

#### `_execute_and_get_result(answer_sql, problem_id, limit=1000)`
Executes SQL against PostgreSQL and converts result to JSON-serializable format:
- Wraps query with LIMIT to prevent huge results
- Converts datetime objects to ISO strings
- Converts numpy types to native Python types
- Returns list of dicts

## Integration Points

### Modified in `generate_daily_problems()`
**Line 70**: Added call to `enrich_problem_with_ai_solution()` after problem creation
```python
problem = enrich_problem_with_ai_solution(problem, scenario)
```

This ensures ALL problems (both PA and Stream) get AI-generated solutions before being saved.

### Automatic Propagation
Changes automatically apply to:
1. `backend/generator/daily_challenge_writer.py` - Uses `generate_daily_problems()`
2. `backend/api/admin.py` - Calls `generate_and_save_daily_challenge()`
3. Cloud Scheduler triggers - Via admin API
4. Local APScheduler - Via admin API

## Database Storage

### Problems are saved with:
- `answer_sql`: Full SQL query (TEXT)
- `expected_result`: JSON array stored in hints field
- `expected_row_count`: Integer (derived)

### Storage locations:
1. **PostgreSQL**: `public.problems` table (primary source)
2. **JSON files**: `problems/daily/{date}.json` (backup/compatibility)
3. **DB table**: `public.daily_challenges` (consolidated)

## Grading Service Integration

The grading service (`backend/services/grading_service.py:238-264`) now uses:
1. `expected_result` from JSON (if present)
2. `answer_sql` executed in real-time (if expected_result missing)
3. Fallback to grading table (legacy support)

## Performance Considerations

### AI Call Timing
- Each problem requires 1 Gemini API call (~2-5 seconds)
- Total for 12 problems: ~24-60 seconds
- Model: Gemini 2.0 Flash (fast, cost-effective)

### SQL Execution
- Each answer_sql executed once during generation
- Results cached in expected_result
- Limit of 1000 rows prevents memory issues

### Token Usage
Estimated per problem:
- Input: ~800-1200 tokens (prompt with schema)
- Output: ~100-300 tokens (SQL query)
- Total: ~1000-1500 tokens/problem
- Daily total: ~12,000-18,000 tokens (well within free tier)

## Error Recovery

### Graceful Degradation
If AI enrichment fails for a problem:
1. Warning logged, but generation continues
2. Problem saved without answer_sql
3. Grading falls back to:
   - Grading table lookup
   - Column validation only
   - Syntax checking

### No Single Point of Failure
- Missing answer_sql doesn't break problem loading
- Missing expected_result doesn't break grading
- System remains functional with partial failures

## Code Quality

### Type Hints
All new functions use proper type hints:
```python
def enrich_problem_with_ai_solution(
    problem: dict,
    scenario: BusinessScenario
) -> dict:
```

### Logging
Comprehensive logging at key points:
- AI call start/success/failure
- SQL extraction results
- Execution results
- Row counts

### Clean Code
- Functions are single-purpose
- Clear separation of concerns
- No side effects in helper functions
- Immutable problem dict (creates copy)

## Testing Strategy

### Unit Testing
Test each helper function independently:
```python
test_build_table_schema_text()
test_extract_sql_from_response()
test_execute_and_get_result()
```

### Integration Testing
```python
test_enrich_problem_with_ai_solution()
test_generate_daily_problems_with_enrichment()
```

### Manual Testing
Created `test_unified_generator.py` for manual verification:
- Generates scenario
- Creates problems
- Checks enrichment success rate
- Shows sample results

## Lessons Learned

### 1. Prompt Engineering Critical
The AI prompt must be very specific about:
- Output format (SQL only, no explanations)
- Syntax constraints (PostgreSQL, no semicolons)
- Context (table schemas, business scenario)
- Column name matching (exact case)

### 2. Robust Extraction Needed
Gemini sometimes wraps SQL in code blocks, sometimes doesn't. Need flexible extraction.

### 3. Date Ranges Matter
Must explicitly tell AI to use dates within scenario.data_period, otherwise it invents dates.

### 4. Error Handling First
Design for failure from the start - missing answer_sql should not break anything.

### 5. Logging is Essential
Detailed logs make debugging AI issues much easier (bad prompts, extraction failures, SQL errors).

## Future Enhancements

### Potential Improvements
1. **Prompt A/B Testing**: Test different prompt formats for better SQL quality
2. **SQL Validation**: Pre-execution syntax check using sqlparse
3. **Query Optimization**: AI could suggest index hints
4. **Multi-Language Support**: Generate SQL for DuckDB vs PostgreSQL
5. **Difficulty Calibration**: AI estimates actual difficulty based on SQL complexity
6. **Caching**: Cache AI responses to avoid re-generation on retries

### Monitoring Needs
1. Track AI success rate (% of problems with answer_sql)
2. Track SQL execution success rate
3. Measure token usage per problem type
4. Monitor generation time vs. grading accuracy

## Configuration

### Environment Variables Used
- `GEMINI_API_KEY`: API key for Gemini
- `GEMINI_MODEL_PROBLEM`: Model for problem generation (default: gemini-flash-latest)
- `POSTGRES_DSN`: Database connection for SQL execution

### Model Selection
Using `GeminiModels.PROBLEM` which maps to Gemini 2.0 Flash:
- Fast (2-3 sec/request)
- Cost-effective
- Good at code generation
- Within free tier limits

## References

### Related Files
- `backend/generator/unified_problem_generator.py` - Main implementation
- `backend/generator/daily_challenge_writer.py` - Uses generator
- `backend/services/grading_service.py` - Consumes answer_sql
- `problems/generator.py` - Legacy generator (similar pattern)
- `problems/gemini.py` - Gemini client wrapper

### Similar Implementations
- `problems/generator.py:get_expected_result()` - Same SQL execution pattern
- `backend/services/ai_service.py` - Similar Gemini integration
- `problems/prompt.py` - Similar prompt construction

## Conclusion

Successfully implemented AI-powered SQL generation that:
✅ Generates answer_sql for all problems
✅ Creates expected_result by executing SQL
✅ Handles errors gracefully (fallback support)
✅ Integrates with existing grading flow
✅ Maintains backward compatibility
✅ Logs comprehensively
✅ Uses type hints and clean code
✅ Minimizes API costs

The implementation follows existing patterns in the codebase and adds value without breaking existing functionality.
