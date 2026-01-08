# problems/prompt_pa.py
"""
Gemini 문제 생성 프롬프트 - Product Type별 맞춤형
"""
from __future__ import annotations

from backend.generator.product_config import (
    get_events_for_type, 
    get_kpi_guide,
    PRODUCT_KPI_GUIDE
)


# Product Type별 요청자 및 문제 유형 매핑
PRODUCT_TYPE_CONTEXTS = {
    "commerce": {
        "name": "이커머스 플랫폼",
        "requesters": [
            ("PM팀", "신규 상품 상세 페이지의 전환율을 알고 싶습니다"),
            ("마케팅팀", "채널별 구매 전환율을 비교해주세요"),
            ("경영진", "이번 달 GMV 추이를 분석해주세요"),
            ("CX팀", "장바구니 이탈 고객의 행동 패턴이 궁금합니다"),
            ("그로스팀", "쿠폰 적용 시 전환율 변화를 분석해주세요"),
            ("SCM팀", "재구매율이 높은 상품군을 파악해주세요"),
        ],
        "topics": [
            "퍼널 분석 (view → purchase 전환율, 이탈 구간)",
            "장바구니 이탈 분석 (cart abandonment)",
            "쿠폰 효과 분석 (apply_coupon → purchase)",
            "재구매 분석 (reorder, repeat purchase)",
            "상품 비교 행동 분석 (compare_product)",
            "매출 분석 (GMV, AOV, ARPU)",
        ],
    },
    "content": {
        "name": "콘텐츠/미디어 플랫폼",
        "requesters": [
            ("PM팀", "콘텐츠 완독률을 분석해주세요"),
            ("에디터팀", "어떤 콘텐츠가 공유가 많이 되는지 알고 싶습니다"),
            ("마케팅팀", "구독 전환에 영향을 주는 행동을 분석해주세요"),
            ("경영진", "DAU와 Reading Time 추이를 보고해주세요"),
            ("그로스팀", "스크롤 깊이별 이탈률을 파악해주세요"),
            ("광고팀", "engagement가 높은 사용자 세그먼트를 찾아주세요"),
        ],
        "topics": [
            "완독률 분석 (scroll_100 / read_content)",
            "스크롤 깊이 분석 (scroll_25/50/75/100 비율)",
            "구독 전환 분석 (subscribe)",
            "공유 행동 분석 (share)",
            "콘텐츠 소비 패턴 (읽기 시간, 세션당 콘텐츠 수)",
            "Engagement 분석 (like + comment + share)",
        ],
    },
    "saas": {
        "name": "B2B SaaS 플랫폼",
        "requesters": [
            ("PM팀", "신규 기능의 Adoption Rate를 측정해주세요"),
            ("CS팀", "Churn 위험 고객을 사전 식별하고 싶습니다"),
            ("세일즈팀", "Upgrade 가능성이 높은 계정을 분석해주세요"),
            ("경영진", "WAU와 Feature Usage 트렌드를 보고해주세요"),
            ("그로스팀", "Activation 이벤트를 정의하고 측정해주세요"),
            ("플랫폼팀", "API 사용량 상위 고객을 분석해주세요"),
        ],
        "topics": [
            "Activation 분석 (onboarding_complete → feature_use)",
            "Feature Adoption 분석 (feature_use 패턴)",
            "Churn 예측 (cancel_subscription 전 행동)",
            "Upgrade 전환 분석 (upgrade_plan)",
            "협업 패턴 분석 (invite_member, create_project)",
            "WAU/MAU 분석 (Active User 정의)",
        ],
    },
    "community": {
        "name": "소셜/커뮤니티 플랫폼",
        "requesters": [
            ("PM팀", "Creator vs Consumer 비율을 분석해주세요"),
            ("커뮤니티팀", "활성 사용자 정의를 세워주세요"),
            ("트러스트팀", "신고 패턴을 분석해주세요"),
            ("경영진", "DAU와 Engagement 추이를 보고해주세요"),
            ("그로스팀", "Viral Loop를 분석해주세요 (follow → post → like)"),
            ("마케팅팀", "인플루언서 세그먼트를 정의해주세요"),
        ],
        "topics": [
            "Creator/Consumer 비율 분석",
            "Engagement Rate 분석 (like + comment / view_feed)",
            "Viral 분석 (follow 체인, share)",
            "활성 사용자 정의 (DAC - Daily Active Creator)",
            "포스팅 패턴 분석 (post_create 시간대, 빈도)",
            "팔로우 네트워크 분석",
        ],
    },
    "fintech": {
        "name": "핀테크/금융 서비스",
        "requesters": [
            ("리스크팀", "송금 실패율이 높은 세그먼트를 분석해주세요"),
            ("컴플라이언스팀", "KYC 완료율을 분석해주세요"),
            ("PM팀", "신규 투자 상품 조회 패턴을 분석해주세요"),
            ("경영진", "월간 거래량과 거래액 추이를 보고해주세요"),
            ("그로스팀", "첫 송금까지의 Time to Value를 측정해주세요"),
            ("FDS팀", "이상 거래 탐지를 위한 행동 패턴을 분석해주세요"),
        ],
        "topics": [
            "거래 성공률 분석 (transfer_success / transfer_attempt)",
            "거래 실패 원인 분석 (transfer_fail)",
            "KYC 완료율 분석",
            "Cross-sell 분석 (loan_apply, investment_view)",
            "사기 탐지 패턴 분석 (fraud_alert_view)",
            "거래량/거래액 분석",
        ],
    },
}


def build_pa_prompt(data_summary: str, n: int = 6, product_type: str = "commerce") -> str:
    """
    Product Type별 맞춤형 SQL 분석 문제 생성 프롬프트
    """
    context = PRODUCT_TYPE_CONTEXTS.get(product_type, PRODUCT_TYPE_CONTEXTS["commerce"])
    events = get_events_for_type(product_type)
    kpi_guide = get_kpi_guide(product_type)
    
    # 요청자/주제 예시 생성
    requesters_str = "\n".join([f"- {r[0]}: \"{r[1]}\"" for r in context["requesters"]])
    topics_str = "\n".join([f"- {t}" for t in context["topics"]])
    events_str = ", ".join(events)
    metrics_str = ", ".join(kpi_guide.get("key_metrics", []))
    mistakes_str = "\n".join([f"- {m}" for m in kpi_guide.get("common_mistakes", [])])
    
    return f"""
너는 {context['name']}의 시니어 데이터 분석가다.
아래 데이터를 기반으로 **실무 SQL 분석 문제와 정답**을 출제하라.

[Product Type]
{product_type.upper()} - {context['name']}

[데이터 요약]
{data_summary}

[사용 가능한 이벤트]
{events_str}

[출제 요구사항]
1. 총 {n}개 문제
2. 난이도 분배: easy 2개, medium 2개, hard 2개
3. **반드시 다른 팀/직무가 요청하는 형태**로 작성
4. **answer_sql은 반드시 위 데이터 스키마에 맞게 작성** (실제 실행 가능해야 함)
5. **{product_type.upper()} 프로덕트 특성에 맞는 문제만 출제**

[{context['name']} 핵심 KPI]
North Star: {kpi_guide.get('north_star', 'N/A')}
Activation: {kpi_guide.get('activation_event', 'N/A')} ({kpi_guide.get('activation_criteria', '')})
주요 지표: {metrics_str}

[문제 유형 (반드시 이 중에서 출제)]
{topics_str}

[요청자 예시]
{requesters_str}

[흔히 틀리는 분석 (문제에 반영)]
{mistakes_str}

[JSON 스키마 - 반드시 준수]
{{
  "problem_id": "startup_sql_001",
  "difficulty": "easy | medium | hard",
  "topic": "retention | funnel | cohort | revenue | segmentation | activation | engagement",
  "requester": "요청팀 또는 직무 (예: PM팀, 마케팅팀)",
  "question": "실제 업무 요청처럼 작성. 반드시 다음을 명시: 1)필요한 컬럼 2)정렬 기준 3)기간/조건",
  "context": "배경 설명 (왜 이 분석이 필요한지)",
  "submission_requirements": "제출 조건을 다음 형식으로 구체적으로 명시 (모든 항목 필수):
    1. 결과 컬럼: 'user_id, conversion_rate, total_amount' 순서로 출력
    2. 날짜 형식: 'YYYY-MM-DD' 형식 (예: DATE_TRUNC('day', timestamp)::date)
    3. 숫자 형식: 소수점 2자리까지 반올림 (예: ROUND(rate, 2))
    4. 정렬: date 컬럼 기준 오름차순 정렬
    5. NULL 처리: NULL 값은 0으로 표시",
  "answer_sql": "PostgreSQL 정답 SQL (위 데이터 스키마의 테이블명/컬럼명 정확히 사용)",
  "expected_description": "기대 결과 테이블 설명",
  "expected_columns": ["col1", "col2", "..."],
  "sort_keys": ["정렬 기준 컬럼 - 필수"],
  "hint": "SQL 작성 힌트 (사용해야 할 함수, 조인 방법 등)"
}}

[데이터 스키마 - answer_sql 작성 시 반드시 사용]
- pa_users: user_id, signup_at, country, channel
- pa_sessions: session_id, user_id, started_at, device
- pa_events: event_id, user_id, session_id, event_time, event_name
- pa_orders: order_id, user_id, order_time, amount

[event_name 값 (위 스키마의 pa_events.event_name)]
{events_str}

[CRITICAL - submission_requirements 작성 가이드]
**반드시 모든 문제에 다음 5가지 항목을 구체적으로 명시하라:**

1. **결과 컬럼**: 출력할 컬럼명과 순서를 정확히 나열
   - ❌ 나쁜 예: "날짜와 전환율을 보여주세요"
   - ✅ 좋은 예: "date, conversion_rate, user_count 순서로 출력"

2. **날짜 형식**: 날짜/시간 컬럼의 정확한 형식 지정
   - ❌ 나쁜 예: "날짜별로 집계"
   - ✅ 좋은 예: "날짜는 YYYY-MM-DD 형식으로 출력 (예: 2026-01-08)"

3. **숫자 형식**: 소수점 자릿수 명시
   - ❌ 나쁜 예: "비율을 계산하세요"
   - ✅ 좋은 예: "비율은 소수점 2자리까지 반올림 (예: 0.15 → 15.00%가 아닌 0.15)"

4. **정렬**: 정렬 기준과 방향 명시
   - ❌ 나쁜 예: "정렬해주세요"
   - ✅ 좋은 예: "date 컬럼 기준 오름차순 정렬, conversion_rate 기준 내림차순 정렬"

5. **NULL/결측값 처리**: NULL 값 처리 방법 명시
   - ❌ 나쁜 예: "값이 없으면 처리"
   - ✅ 좋은 예: "NULL 값은 0으로 표시, 데이터가 없는 날짜는 결과에서 제외"

[중요 - 문제 명확성]
- **{product_type.upper()} 프로덕트 관점**에서 문제 출제
- purchase 중심이 아닌, **{kpi_guide.get('activation_event', '핵심 이벤트')} 중심**으로 사고
- 문제는 **다른 팀에서 슬랙으로 요청하는 톤**으로 작성하되, 업무 내용은 명확하게
- **submission_requirements**는 위 5가지 항목을 반드시 모두 포함하여 구체적으로 작성
- answer_sql은 **위 테이블/컬럼만 사용**하여 실제 실행 가능하게 작성
- answer_sql의 결과가 submission_requirements와 100% 일치하도록 작성
- JSON 배열 형식으로만 출력
""".strip()



def build_pa_review_prompt(
    problem: dict,
    user_sql: str,
    is_correct: bool,
    error_message: str | None,
) -> str:
    """채점 피드백 프롬프트"""
    return f"""
너는 시니어 데이터 분석가다.
아래는 주니어 분석가가 제출한 SQL이다.

[문제]
{problem.get("question", "")}

[요청 배경]
{problem.get("context", "없음")}

[사용자 SQL]
{user_sql}

[정답 여부]
{"정답" if is_correct else "오답"}

[에러 메시지]
{error_message or "없음"}

[피드백 작성 기준]
1. 정답이든 오답이든 **실무 시니어처럼** 피드백
2. 오답이면 틀린 이유와 올바른 접근법 설명
3. 정답이어도 더 나은 방법이 있으면 제안
4. 쿼리 성능, 가독성, 실무 관례 관점 피드백
5. 이 분석을 실무에서 어떻게 활용할 수 있는지 팁
6. 친근하지만 전문적인 톤

[출력 형식]
마크다운, 항목별로 구분
""".strip()
