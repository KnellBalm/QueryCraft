from __future__ import annotations

import os

PROMPT_VERSION = os.getenv("PROMPT_VERSION", "v1")

SUBMISSION_REQUIREMENTS_TEMPLATE = """아래 템플릿 형식 그대로 작성 (순서/라벨 고정, 예시 포함):
    1. 결과 컬럼: <col1, col2, ...> 순서로 출력
    2. 집계 단위: <일별(Daily) | 월별(Monthly) | 주별(Weekly)>
    3. 날짜 형식: <YYYY-MM-DD 또는 YYYY-MM> (예: 2026-01-08 또는 2026-01)
    4. 숫자 형식: <소수점 자리/ROUND 규칙>
    5. 정렬: <정렬 기준 컬럼 및 방향>
    6. NULL 처리: <NULL 처리 방식>"""

DATE_FORMAT_GUIDANCE = """[날짜 형식 엄수]
- 분석 단위에 따라 날짜 포맷을 **명시하고 예시 포함**
- 일별(Daily) → **YYYY-MM-DD** (예: 2026-01-08)
- 월별(Monthly) → **YYYY-MM** (예: 2026-01)
- 주별(Weekly) → **YYYY-MM-DD** (주 시작일 기준, 예: 2026-01-05)
- 문제에 명시된 포맷과 **answer_sql 출력 포맷이 100% 일치**해야 함
- 데이터 요약에 나온 날짜 범위를 벗어나지 말 것"""
