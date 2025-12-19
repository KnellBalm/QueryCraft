# problems/prompt_stream.py
from __future__ import annotations

def build_stream_prompt(data_summary: str) -> str:
    """
    Stream 로그 기반 실무형 분석 '업무 요청서' 생성 프롬프트
    """

    return f"""
너는 회사의 시니어 데이터 분석가다.

아래는 오늘 기준 서비스 로그 데이터 요약이다.
이 데이터는 실제 사용자 행동 로그를 기반으로 한다.

[데이터 요약]
{data_summary}

이 데이터를 기반으로,
신입 데이터 분석가에게 실제로 업무를 지시하듯
'분석 업무 요청서'를 작성하라.

요구사항:
- 총 {n}개의 업무 요청서를 작성한다
- 각 요청서는 서로 다른 관점을 가져야 한다
- 문제나 퀴즈처럼 보이지 않도록 한다
- SQL, 쿼리, 정답, 계산식은 절대 작성하지 않는다
- 실제 회사에서 사용하는 업무 톤을 사용한다

각 업무 요청서는 반드시 아래 JSON 구조를 따른다:

{{
  "task_id": "...",
  "domain": "marketing | product | growth | ops",
  "difficulty": "easy | medium | advanced",
  "context": "왜 이 분석이 필요한지에 대한 배경 설명",
  "request": [
    "분석을 통해 확인해야 할 질문 1",
    "분석을 통해 확인해야 할 질문 2"
  ],
  "constraints": [
    "기간 조건",
    "필터 조건",
    "주의 사항"
  ],
  "deliverables": [
    "결과로 기대하는 테이블 형태 또는 지표",
    "해석 또는 인사이트 요구 사항"
  ]
}}

JSON 배열 형식으로만 출력하라.
""".strip()

def build_stream_review_prompt(
    task: dict,
    user_sql: str,
    user_notes: str | None,
) -> str:
    return f"""
아래는 분석 업무 요청과 사용자의 분석 결과이다.

[업무 요청]
{task}

[사용자 SQL]
{user_sql}

[사용자 해석]
{user_notes or "없음"}

이 분석을 리뷰하라.
- 요청을 제대로 충족했는가
- 부족한 분석 관점
- 추가로 보면 좋을 지표

서술형으로 피드백하라.
""".strip()
