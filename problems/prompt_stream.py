# problems/prompt_stream.py
"""
Stream 문제 생성 프롬프트 - prompt.py에서 호출
통합 generator 아키텍처의 일부
"""
from __future__ import annotations

from backend.engine.postgres_engine import PostgresEngine
from backend.config.db import PostgresEnv
from backend.common.logging import get_logger

logger = get_logger(__name__)


def get_stream_data_summary() -> str:
    """Stream 데이터 요약 생성 - Gemini에게 정확한 스키마 정보 제공"""
    pg = PostgresEngine(PostgresEnv().dsn())
    try:
        summary_lines = ["## 테이블 구조 (PostgreSQL - Stream 분석용)"]

        tables_info = [
            ("stream_events", "user_id (INT), session_id (TEXT), event_name (TEXT), event_time (TIMESTAMP), device (TEXT), channel (TEXT)"),
            ("stream_daily_metrics", "date (DATE), revenue (FLOAT), purchases (INT)")
        ]

        for table_name, columns in tables_info:
            try:
                df = pg.fetch_df(f"SELECT COUNT(*) as cnt FROM public.{table_name}")
                count = int(df.iloc[0]["cnt"])
                summary_lines.append(f"- {table_name}: {count:,}건")
                summary_lines.append(f"  컬럼: {columns}")
            except Exception as e:
                summary_lines.append(f"- {table_name}: 조회 불가 ({e})")

        # 이벤트 유형
        try:
            df = pg.fetch_df("SELECT DISTINCT event_name FROM public.stream_events LIMIT 10")
            event_names = [row["event_name"] for _, row in df.iterrows()]
            summary_lines.append(f"\n## 이벤트 유형 (event_name)")
            summary_lines.append(", ".join(event_names))
        except Exception:
            pass

        # 날짜 범위
        try:
            date_df = pg.fetch_df("""
                SELECT
                    MIN(event_time)::date as min_date,
                    MAX(event_time)::date as max_date
                FROM public.stream_events
            """)
            min_date = date_df.iloc[0]["min_date"]
            max_date = date_df.iloc[0]["max_date"]
            summary_lines.append(f"\n## 데이터 날짜 범위")
            summary_lines.append(f"- 이벤트: {min_date} ~ {max_date}")
        except Exception:
            pass

        summary_lines.append("\n## 주의사항")
        summary_lines.append("- answer_sql은 반드시 위 테이블/컬럼만 사용")
        summary_lines.append("- 날짜 조건은 위 데이터 범위 내에서 사용")

        return "\n".join(summary_lines)
    except Exception as e:
        logger.error(f"Failed to get stream data summary: {e}")
        return "## Stream 데이터 요약 실패"
    finally:
        pg.close()


def build_stream_prompt(data_summary: str, n: int = 6, product_type: str = "commerce") -> str:
    """
    Stream SQL 문제 생성 프롬프트 (통합 generator용)

    Args:
        data_summary: Stream 데이터 요약
        n: 생성할 문제 수 (기본 6)
        product_type: 현재 Product Type (commerce, saas, fintech, content, community)

    Returns:
        Gemini API 호출용 프롬프트 문자열
    """
    return f"""
너는 스트리밍 광고/마케팅 데이터 분석 전문가다.
아래 Stream 데이터를 기반으로 **실무 SQL 분석 문제와 정답**을 출제하라.

[데이터 요약]
{data_summary}

[출제 요구사항]
1. 총 {n}개 문제
2. 난이도 분배: easy 2개, medium 2개, hard 2개
3. 주제: 퍼널 분석, 일별 매출 추이, 채널별 성과, 디바이스별 전환율, DAU/MAU 등
4. **반드시 다른 팀/직무가 요청하는 형태**로 작성
5. **submission_requirements**를 아래 5가지 항목 모두 포함하여 구체적으로 작성

[JSON 스키마]
{{
  "problem_id": "stream_sql_001",
  "difficulty": "easy | medium | hard",
  "topic": "funnel | revenue | dau | channel | device",
  "requester": "요청팀",
  "question": "업무 요청 형태로 작성. 필요 컬럼, 정렬 기준 명시",
  "context": "배경 설명",
  "submission_requirements": "제출 조건을 다음 형식으로 구체적으로 명시 (모든 항목 필수):
    1. 결과 컬럼: 'date, revenue, user_count' 순서로 출력
    2. 날짜 형식: 'YYYY-MM-DD' 형식 (예: DATE_TRUNC('day', event_time)::date)
    3. 숫자 형식: 소수점 2자리까지 반올림 (예: ROUND(rate::numeric, 2))
    4. 정렬: date 컬럼 기준 오름차순 정렬
    5. NULL 처리: NULL 값은 0으로 표시",
  "answer_sql": "PostgreSQL 정답 SQL",
  "expected_columns": ["col1", "col2"],
  "sort_keys": ["정렬 기준 컬럼"],
  "hint": "문제 해결 접근법 힌트 (예: '먼저 날짜별로 그룹화하고, 전환율을 계산한 후, 상위 N개를 추출하세요')"
}}

[CRITICAL - submission_requirements 작성 가이드]
**반드시 모든 문제에 다음 5가지 항목을 구체적으로 명시하라:**

1. **결과 컬럼**: 출력할 컬럼명과 순서를 정확히 나열
   - ❌ 나쁜 예: "날짜와 매출을 보여주세요"
   - ✅ 좋은 예: "date, revenue, user_count 순서로 출력"

2. **날짜 형식**: 날짜/시간 컬럼의 정확한 형식 지정
   - ❌ 나쁜 예: "날짜별로 집계"
   - ✅ 좋은 예: "날짜는 YYYY-MM-DD 형식으로 출력 (예: 2026-01-08)"

3. **숫자 형식**: 소수점 자릿수 명시
   - ❌ 나쁜 예: "전환율을 계산하세요"
   - ✅ 좋은 예: "비율은 소수점 2자리까지 반올림 (예: 0.15)"

4. **정렬**: 정렬 기준과 방향 명시
   - ❌ 나쁜 예: "정렬해주세요"
   - ✅ 좋은 예: "date 컬럼 기준 오름차순 정렬"

5. **NULL/결측값 처리**: NULL 값 처리 방법 명시
   - ❌ 나쁜 예: "값이 없으면 처리"
   - ✅ 좋은 예: "NULL 값은 0으로 표시, 데이터가 없는 날짜는 결과에서 제외"

[중요]
- answer_sql은 **위 테이블/컬럼만 사용**
- answer_sql의 결과가 submission_requirements와 100% 일치하도록 작성
- submission_requirements는 위 5가지 항목을 반드시 모두 포함
- JSON 배열 형식으로만 출력
""".strip()


# ============================================================
# Legacy functions (보존 - 하위 호환성)
# ============================================================

def build_stream_task_prompt(data_summary: str, n: int = 6) -> str:
    """
    [DEPRECATED] Stream 로그 기반 실무형 분석 '업무 요청서' 생성 프롬프트
    새로운 코드에서는 build_stream_prompt()를 사용하세요.
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
