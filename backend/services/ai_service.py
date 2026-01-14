# backend/services/ai_service.py
from __future__ import annotations

import json
from problems.gemini import _call_gemini_with_retry, GeminiModels
from backend.services.problem_service import get_problem_by_id, get_table_schema
from backend.common.logging import get_logger

logger = get_logger(__name__)

def get_ai_insight(problem_id: str, sql: str, results: list[dict], data_type: str = "pa") -> str:
    """SQL 실행 결과를 바탕으로 AI 인사이트 생성"""
    problem = get_problem_by_id(problem_id, data_type)
    schema = get_table_schema("stream_" if data_type == "stream" else "pa_")
    
    # 결과 데이터 요약 (너무 크면 자름)
    sample_data = results[:20] if results else []
    
    prompt = f"""
너는 숙련된 데이터 분석가이자 비즈니스 전략가다.
사용자가 작성한 SQL 쿼리와 그 실행 결과를 분석하여 비즈니스 인사이트와 액션 플랜을 제안하라.

[분석 맥락]
- 문제: {problem.title if problem else "비공개 분석"}
- 질문: {problem.question if problem else "데이터 탐색"}
- 사용된 SQL:
```sql
{sql}
```

[실행 결과 (상위 20개 샘플)]
{json.dumps(sample_data, ensure_ascii=False, indent=2)}

[데이터 스키마 정보]
{schema}

[요청 사항]
1. 위 데이터를 바탕으로 발견할 수 있는 핵심 인사이트(Fact & Insight)를 3가지 이내로 요약하라.
2. 발견된 문제점이나 기회 요인을 바탕으로 구체적인 '비즈니스 액션 플랜'을 제안하라.
3. 분석가다운 전문적인 톤을 유지하되, 이해하기 쉽게 설명하라.
4. 결과는 마크다운 형식으로 작성하라.

[출력 형식]
### 📊 핵심 인사이트
- ...
### 💡 액션 플랜 (Action Plan)
- ...
"""

    try:
        response = _call_gemini_with_retry(
            model=GeminiModels.PROBLEM, # 인사이트는 추론 능력이 좋은 모델 사용
            contents=prompt,
            purpose="ai_insight"
        )
        return response.text.strip()
    except Exception as e:
        logger.error(f"Failed to get AI insight: {e}")
        return "인사이트를 생성하는 중 오류가 발생했습니다."

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
