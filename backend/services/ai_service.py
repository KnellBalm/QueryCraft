# backend/services/ai_service.py
from __future__ import annotations

import json
from problems.gemini import _call_gemini_with_retry, GeminiModels
from backend.services.problem_service import get_problem_by_id, get_table_schema
from backend.common.logging import get_logger

logger = get_logger(__name__)

def get_ai_insight(problem_id: str, sql: str, results: list[dict], data_type: str = "pa") -> dict:
    """SQL 실행 결과를 바탕으로 AI 인사이트 생성 (구조화된 JSON 반환)"""
    problem = get_problem_by_id(problem_id, data_type)
    schema = get_table_schema("stream_" if data_type == "stream" else "pa_")
    
    # 결과 데이터 요약 (너무 크면 자름)
    sample_data = results[:20] if results else []
    
    prompt = f"""
당신은 데이터 분석 결과를 비즈니스 인사이트로 변환하는 전문가입니다.

**입력 데이터**:
```
{json.dumps(sample_data, ensure_ascii=False, indent=2)}
```

**실행한 SQL**:
```sql
{sql}
```

**데이터 스키마**:
{schema}

**요구사항**:
1. **핵심 발견 (Key Findings)**: 데이터에서 발견한 정량적 사실 3가지
2. **비즈니스 인사이트**: 발견의 의미와 배경 해석
3. **추천 액션**: 구체적이고 실행 가능한 액션 아이템
4. **추가 분석 제안**: 더 깊이 파고들 수 있는 SQL 쿼리 제안 (제목 + 쿼리)

**출력 형식**: JSON만 출력하세요. 다른 텍스트는 포함하지 마세요.
{{
  "key_findings": ["문장1", "문장2", "문장3"],
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
        report_md = f"""# AI 인사이트 리포트

## 📌 핵심 발견 (Key Findings)
{chr(10).join(f"{i+1}. {finding}" for i, finding in enumerate(parsed.get('key_findings', [])))}

## 💡 비즈니스 인사이트
{chr(10).join(f"- {insight}" for insight in parsed.get('insights', []))}

## 🎯 추천 액션 (Action Items)
{chr(10).join(f"{i+1}. {action}" for i, action in enumerate(parsed.get('action_items', [])))}

## 🔍 추가 분석 제안
{chr(10).join(f"### {q['title']}\n```sql\n{q['sql']}\n```\n" for q in parsed.get('suggested_queries', []))}
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
        logger.error(f"Raw response: {raw_text[:500]}")
        return {
            "key_findings": [],
            "insights": [],
            "action_items": [],
            "suggested_queries": [],
            "report_markdown": "# 오류\n\nAI 인사이트를 파싱하는 중 오류가 발생했습니다.",
            "insight": raw_text  # 하위 호환
        }
    except Exception as e:
        logger.error(f"Failed to get AI insight: {e}")
        return {
            "key_findings": [],
            "insights": [],
            "action_items": [],
            "suggested_queries": [],
            "report_markdown": "# 오류\n\n인사이트를 생성하는 중 오류가 발생했습니다.",
            "insight": "인사이트를 생성하는 중 오류가 발생했습니다."  # 하위 호환
        }

def translate_text_to_sql(question: str, data_type: str = "pa") -> str:
    """자연어 질문을 SQL로 변환"""
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
4. 출력은 반드시 SQL 코드 블록만 포함하라. 부연 설명은 하지 마라.

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
            return sql_match.group(1).strip()
        
        # 코드 블록이 없는 경우 전체 텍스트 반환 (가급적 SQL만 주도록 프롬프트 작성됨)
        return raw_text
    except Exception as e:
        logger.error(f"Failed to translate text to SQL: {e}")
        return "-- SQL 변환 중 오류가 발생했습니다."


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

