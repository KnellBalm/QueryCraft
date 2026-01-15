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
