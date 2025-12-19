# problems/prompt_pa.py
from __future__ import annotations

def build_pa_prompt(data_summary: str, n: int) -> str:
    return f"""
너는 데이터 분석팀의 시니어 분석가다.

아래는 오늘 기준 서비스 데이터 요약이다.

[데이터 요약]
{data_summary}

이 데이터를 기반으로
SQL 실무 연습용 문제를 작성하라.

요구사항:
- 총 {n}개 문제
- beginner / intermediate / advanced 난이도를 고르게 포함
- 실무에서 실제로 시키는 분석 과제 톤
- 각 문제는 SQL로 정확한 결과를 도출할 수 있어야 한다
- 정답 SQL은 작성하지 말 것

각 문제는 반드시 아래 JSON 구조를 따른다.

{{
  "problem_id": "...",
  "difficulty": "beginner | intermediate | advanced",
  "topic": "retention | funnel | cohort | revenue | segmentation",
  "question": "실무 분석 요청 형태의 문제 설명",
  "expected_description": "결과 테이블이 어떤 의미인지 서술",
  "expected_columns": ["col1", "col2", "..."],
  "sort_keys": ["optional"]
}}

JSON 배열 형식으로만 출력하라.
""".strip()

def build_pa_review_prompt(
    problem: dict,
    user_sql: str,
    is_correct: bool,
    error_message: str | None,
) -> str:
    return f"""
아래는 SQL 분석 문제와 사용자의 쿼리이다.

[문제]
{problem["question"]}

[사용자 SQL]
{user_sql}

[정답 여부]
{"정답" if is_correct else "오답"}

[시스템 에러 메시지]
{error_message or "없음"}

이 SQL을 리뷰하라.
- 논리적 오류가 무엇인지
- 실무에서 개선할 점
- 성능/가독성 관점 피드백

서술형으로만 작성하라.
""".strip()
