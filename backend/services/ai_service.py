# backend/services/ai_service.py
from __future__ import annotations

import json
from problems.gemini import _call_gemini_with_retry, GeminiModels
from backend.services.problem_service import get_problem_by_id, get_table_schema
from backend.common.logging import get_logger

logger = get_logger(__name__)

def get_ai_insight(problem_id: str, sql: str, results: list[dict], data_type: str = "pa") -> dict:
    """SQL 실행 결과를 바탕으로 AI 인사이트 생성 (구조화된 JSON 반환)

    개선사항:
    - 문제 컨텍스트(제목, 의도) 추가
    - 빈 결과 처리
    - Gemini API 실패 시 fallback 메시지
    """
    # 문제 정보 조회
    problem = get_problem_by_id(problem_id, data_type)
    schema = get_table_schema("stream_" if data_type == "stream" else "pa_")

    # 결과 데이터 요약 (너무 크면 자름)
    sample_data = results[:20] if results else []

    # 빈 결과 처리
    if not sample_data:
        logger.info(f"Empty results for problem {problem_id}, returning default insight")
        return {
            "key_findings": ["쿼리 실행 결과가 비어있습니다."],
            "insights": ["결과가 없는 이유를 확인해보세요. WHERE 조건이 너무 엄격하거나, 데이터가 실제로 존재하지 않을 수 있습니다."],
            "action_items": ["쿼리 조건을 완화하거나 데이터 범위를 확인해보세요."],
            "suggested_queries": [],
            "report_markdown": "# 결과 없음\n\n쿼리 실행 결과가 비어있습니다."
        }

    # 문제 컨텍스트 추가
    problem_title = problem.get('title', '제목 없음') if problem else '문제 정보 없음'
    problem_question = problem.get('question', '') if problem else ''

    prompt = f"""
당신은 데이터 분석 결과를 비즈니스 인사이트로 변환하는 전문가입니다.

**문제 컨텍스트**:
- 문제 제목: {problem_title}
- 분석 목적: {problem_question[:200]}

**입력 데이터** (샘플 {len(sample_data)}행):
```json
{json.dumps(sample_data, ensure_ascii=False, indent=2)}
```

**실행한 SQL**:
```sql
{sql}
```

**데이터 스키마**:
{schema}

**요구사항**:
1. **핵심 발견 (Key Findings)**: 데이터에서 발견한 정량적 사실 2-3가지
2. **비즈니스 인사이트**: 발견의 의미와 비즈니스적 해석 (문제 컨텍스트 고려)
3. **추천 액션**: 구체적이고 실행 가능한 액션 아이템 2-3개
4. **추가 분석 제안**: 더 깊이 파고들 수 있는 SQL 쿼리 제안 1-2개 (제목 + 쿼리)

**출력 형식**: JSON만 출력하세요. 다른 텍스트는 포함하지 마세요.
{{
  "key_findings": ["문장1", "문장2"],
  "insights": ["인사이트1", "인사이트2"],
  "action_items": ["액션1", "액션2"],
  "suggested_queries": [
    {{"title": "제목", "sql": "SELECT ..."}}
  ]
}}
"""

    try:
        response = _call_gemini_with_retry(
            model=GeminiModels.PROBLEM,  # 인사이트는 추론 능력이 좋은 모델 사용
            contents=prompt,
            purpose="ai_insight"
        )
        
        # JSON 파싱
        raw_text = response.text.strip()
        
        # JSON 블록 추출 시도
        import re
        json_match = re.search(r'```json\s*(.*?)\s*```', raw_text, re.DOTALL | re.IGNORECASE)
        if json_match:
            json_text = json_match.group(1).strip()
        else:
            # 블록이 없으면 전체 텍스트에서 JSON 파싱 시도
            json_text = raw_text
        
        # JSON 파싱
        parsed = json.loads(json_text)
        
        # 마크다운 리포트 생성
        findings_md = "\n".join(f"{i+1}. {finding}" for i, finding in enumerate(parsed.get('key_findings', [])))
        insights_md = "\n".join(f"- {insight}" for insight in parsed.get('insights', []))
        actions_md = "\n".join(f"{i+1}. {action}" for i, action in enumerate(parsed.get('action_items', [])))
        
        suggested_parts = []
        for q in parsed.get('suggested_queries', []):
            suggested_parts.append(f"### {q['title']}\n```sql\n{q['sql']}\n```")
        suggested_md = "\n".join(suggested_parts)

        report_md = f"""# AI 인사이트 리포트

## 📌 핵심 발견 (Key Findings)
{findings_md}

## 💡 비즈니스 인사이트
{insights_md}

## 🎯 추천 액션 (Action Items)
{actions_md}

## 🔍 추가 분석 제안
{suggested_md}
"""
        
        return {
            "key_findings": parsed.get('key_findings', []),
            "insights": parsed.get('insights', []),
            "action_items": parsed.get('action_items', []),
            "suggested_queries": parsed.get('suggested_queries', []),
            "report_markdown": report_md
        }
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI insight JSON: {e}")
        logger.error(f"Raw response: {raw_text[:500] if 'raw_text' in locals() else 'N/A'}")
        # Fallback: 기본 인사이트 제공
        return {
            "key_findings": [
                "쿼리가 정상적으로 실행되었습니다.",
                f"총 {len(results)}행의 결과가 반환되었습니다."
            ],
            "insights": [
                "AI 인사이트를 생성하는 중 오류가 발생했지만, 쿼리 결과는 정상입니다.",
                "결과 데이터를 직접 확인하여 패턴을 분석해보세요."
            ],
            "action_items": [
                "결과 데이터를 시각화하거나 추가 필터링을 적용해보세요."
            ],
            "suggested_queries": [],
            "report_markdown": f"# AI 인사이트 생성 오류\n\n쿼리는 정상적으로 실행되었으나 ({len(results)}행 반환), AI 분석 중 오류가 발생했습니다.\n\n결과 데이터를 직접 확인해주세요.",
            "insight": raw_text[:500] if 'raw_text' in locals() else ""  # 하위 호환
        }
    except Exception as e:
        logger.error(f"Failed to get AI insight: {e}", exc_info=True)
        # Gemini API 실패 시 fallback
        return {
            "key_findings": [
                "쿼리가 정상적으로 실행되었습니다.",
                f"총 {len(results)}행의 결과가 반환되었습니다."
            ],
            "insights": [
                "AI 서비스가 일시적으로 사용 불가능합니다.",
                "쿼리 결과는 정상적으로 확인할 수 있습니다."
            ],
            "action_items": [
                "잠시 후 다시 시도하거나, 결과를 직접 분석해보세요."
            ],
            "suggested_queries": [],
            "report_markdown": f"# AI 서비스 일시 중단\n\n쿼리는 정상적으로 실행되었으나 ({len(results)}행 반환), AI 인사이트 생성 서비스가 일시적으로 사용 불가능합니다.\n\n에러: {str(e)[:100]}",
            "insight": f"AI 인사이트를 생성하는 중 오류가 발생했습니다: {str(e)[:100]}"  # 하위 호환
        }

def translate_text_to_sql(question: str, data_type: str = "pa") -> str:
    """자연어 질문을 SQL로 변환 (유효성 검증 포함)

    개선사항:
    - 생성된 SQL 유효성 검증 (DuckDB dry-run)
    - 위험한 쿼리 거부 (DROP, DELETE, TRUNCATE, UPDATE, INSERT)
    - 에러 핸들링 강화
    """
    schema = get_table_schema("stream_" if data_type == "stream" else "pa_")

    prompt = f"""
너는 SQL 전문가다. 사용자의 자연어 질문을 PostgreSQL 쿼리로 변환하라.

[데이터 스키마 정보]
{schema}

[사용자 질문]
"{question}"

[주의 사항]
1. 반드시 PostgreSQL 문법을 사용하라.
2. 스키마에 정의된 테이블과 컬럼만 사용하라.
3. 모호한 부분이 있다면 가장 합리적인 추측을 바탕으로 작성하라.
4. SELECT 쿼리만 작성하라. INSERT, UPDATE, DELETE, DROP 등 변경 쿼리는 작성하지 마라.
5. 출력은 반드시 SQL 코드 블록만 포함하라. 부연 설명은 하지 마라.

[출력 형식]
```sql
SELECT ...
```
"""

    try:
        response = _call_gemini_with_retry(
            model=GeminiModels.PROBLEM,
            contents=prompt,
            purpose="text_to_sql"
        )

        # SQL 코드 블록 추출
        raw_text = response.text.strip()
        import re
        sql_match = re.search(r"```sql\s*(.*?)\s*```", raw_text, re.DOTALL | re.IGNORECASE)
        if sql_match:
            generated_sql = sql_match.group(1).strip()
        else:
            # 코드 블록이 없는 경우 전체 텍스트 사용
            generated_sql = raw_text.strip()

        # 위험한 쿼리 검증
        dangerous_keywords = ['DROP', 'DELETE', 'TRUNCATE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 'GRANT', 'REVOKE']
        sql_upper = generated_sql.upper()
        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                logger.warning(f"Dangerous SQL keyword detected: {keyword}")
                return f"-- 보안상의 이유로 {keyword} 쿼리는 지원하지 않습니다.\n-- SELECT 쿼리만 사용해주세요."

        # SQL 유효성 검증 (DuckDB dry-run)
        try:
            from backend.services.database import duckdb_connection
            with duckdb_connection() as duck:
                # EXPLAIN으로 파싱만 검증 (실행하지 않음)
                duck.execute(f"EXPLAIN {generated_sql}")
            logger.info(f"SQL validation passed for: {generated_sql[:50]}...")
        except Exception as validation_error:
            logger.warning(f"SQL validation failed: {validation_error}")
            # 유효성 검증 실패 시에도 SQL 반환 (사용자가 수정 가능)
            return f"{generated_sql}\n\n-- 주의: 생성된 쿼리에 문법 오류가 있을 수 있습니다.\n-- 오류: {str(validation_error)[:100]}"

        return generated_sql

    except Exception as e:
        logger.error(f"Failed to translate text to SQL: {e}", exc_info=True)
        return f"-- SQL 변환 중 오류가 발생했습니다.\n-- 에러: {str(e)[:100]}\n-- 질문을 다시 작성해주세요."


def get_ai_help(
    problem_id: str, 
    help_type: str, 
    current_sql: str = "", 
    attempt_count: int = 0,
    data_type: str = "pa"
) -> dict:
    """
    Daily 문제용 AI 도움 기능
    
    Args:
        problem_id: 문제 ID
        help_type: "hint" 또는 "solution"
        current_sql: 사용자가 작성 중인 SQL
        attempt_count: 현재까지 시도 횟수
        data_type: 문제 타입
        
    Returns:
        {"type": "hint"|"solution", "content": "..."}
    """
    problem = get_problem_by_id(problem_id, data_type)
    if not problem:
        return {"type": "error", "content": "문제를 찾을 수 없습니다."}
    
    schema = get_table_schema("stream_" if data_type == "stream" else "pa_")
    
    if help_type == "hint":
        prompt = f"""
당신은 SQL 튜터입니다. 학생이 문제를 풀고 있습니다.
직접적인 정답을 알려주지 말고, **접근 방향**을 힌트로 제공하세요.

**문제**:
{problem.get('question', '')}

**테이블 스키마**:
{schema}

**학생이 시도한 횟수**: {attempt_count}회
**학생이 작성 중인 SQL**:
```sql
{current_sql if current_sql else '(아직 작성하지 않음)'}
```

**요구사항**:
1. 정답 SQL을 직접 알려주지 마세요.
2. 어떤 테이블을 사용해야 하는지, 어떤 함수가 필요한지 힌트를 주세요.
3. 2-3문장으로 간결하게 작성하세요.
4. 격려하는 톤으로 작성하세요.

힌트:
"""
    else:  # solution
        prompt = f"""
당신은 SQL 전문가입니다. 학생이 문제를 푸는데 어려움을 겪고 있어 정답을 요청했습니다.

**문제**:
{problem.get('question', '')}

**테이블 스키마**:
{schema}

**정답 SQL** (참고용):
```sql
{problem.get('expected_query', '')}
```

**요구사항**:
1. 정답 SQL을 제공하세요.
2. 왜 이렇게 작성해야 하는지 간단히 설명하세요.
3. 핵심 포인트 1-2개를 알려주세요.

형식:
```sql
(정답 쿼리)
```

**설명**: (간단한 설명)
"""

    try:
        response = _call_gemini_with_retry(
            model=GeminiModels.PROBLEM,
            contents=prompt,
            purpose="ai_help"
        )
        
        return {
            "type": help_type,
            "content": response.text.strip()
        }
    except Exception as e:
        logger.error(f"Failed to get AI help: {e}")
        return {
            "type": "error",
            "content": "AI 도움을 생성하는 중 오류가 발생했습니다."
        }

