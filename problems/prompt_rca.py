# problems/prompt_rca.py
"""
Gemini 문제 생성 프롬프트 - RCA (Root Cause Analysis, 원인 분석) 특화
"""
from __future__ import annotations

from backend.generator.product_config import (
    get_events_for_type, 
    get_kpi_guide,
    PRODUCT_KPI_GUIDE
)

# RCA 전용 상황 설정
RCA_SCENARIOS = {
    "commerce": [
        "신규 유입 채널(Social)의 구매 전환율이 전일 대비 30% 급락함. 원인 파악 필요.",
        "특정 카테고리(전자제품)의 장바구니 이탈률이 급증함. 결제 단계의 문제인지 확인 필요.",
        "iOS 업데이트 이후 결제 완료 이벤트 수집이 누락되는 정황 포착.",
    ],
    "content": [
        "지난주 대비 유료 구독 유저의 평균 체류 시간이 15% 감소함. 어떤 변화 때문인가?",
        "신규 콘텐츠 릴리즈 이후 완독률이 비정상적으로 높게 측정됨. 봇 트래픽 여부 확인 필요.",
        "추천 알고리즘 변경 이후 리텐션 지표 하락. 특정 버전에 문제가 있는지 분석 필요.",
    ],
    "saas": [
        "Free-to-Paid 전환율이 갑자기 0으로 떨어짐. 결제 모듈 연동 확인 필요.",
        "특정 기업 고객(Enterprise) 그룹의 API 호출 오류 발생률 급증.",
        "온보딩 완료율은 그대로이나, 첫 번째 기능 수행(Feature Use) 비율이 감소함.",
    ],
    "community": [
        "특정 국가에서 가입자 수는 늘었으나 포스팅 생성 수가 늘지 않음. 스팸 계정 필터링 필요.",
        "모바일 앱 유저들의 피드 조회수(view_feed)가 웹 대비 비정상적으로 낮음.",
        "팔로우 관계는 늘어나는 중이나, 실제 피드 도달률이 떨어지는 원인 분석.",
    ],
    "fintech": [
        "해외 송금 실패율이 특정 시간대를 기점으로 급증함. 망 장애 여부 파악.",
        "계좌 연결(KYC) 완료 단계에서 유저 이탈이 평소보다 2배 높음.",
        "특정 연령대(20대)에서 투자 상품 조회 수는 높으나 실제 매수 전환이 매우 낮음.",
    ]
}

def build_rca_prompt(data_summary: str, n: int = 6, product_type: str = "commerce") -> str:
    """
    RCA(원인 분석) 특화 문제 생성 프롬프트
    """
    events = get_events_for_type(product_type)
    kpi_guide = get_kpi_guide(product_type)
    scenarios = RCA_SCENARIOS.get(product_type, RCA_SCENARIOS["commerce"])
    scenarios_str = "\n".join([f"- {s}" for s in scenarios])
    events_str = ", ".join(events)
    
    return f"""
너는 {product_type.upper()} 프로덕트의 시니어 데이터 분석가다.
현재 시스템에 **비즈니스 장애나 지표 이상 징후(Anomalies)**가 감지되었다.
유저가 SQL을 통해 이 이상 현상의 **근본 원인(Root Cause)**을 찾아낼 수 있도록 실무적인 문제를 출제하라.

[데이터 요약]
{data_summary}

[사용 가능한 이벤트]
{events_str}

[RCA 상황 예시 (이 중 하나 혹은 유사한 상황으로 출제)]
{scenarios_str}

[출제 요구사항]
1. 총 {n}개 문제 (모두 지표 이상이나 문제 해결 중심)
2. 난이도 분배: easy 1개, medium 3개, hard 2개 (원인 분석은 복잡도가 높으므로 medium 비중 상향)
3. **상황 설명은 실제 장애 보고서나 긴급 슬랙 메시지처럼** 긴박하게 작성
4. 유저가 이 문제를 풀고 나면 **"어디서 문제가 발생했는지"**를 명확히 알 수 있어야 함
5. **answer_sql은 반드시 위 데이터 스키마에 맞게 작성** (실제 실행 가능해야 함)

[JSON 스키마]
{{
  "problem_id": "rca_sql_001",
  "difficulty": "easy | medium | hard",
  "topic": "rca | error_analysis | anomaly_detection",
  "requester": "CTO, 경영진, 또는 그로스팀 리더",
  "question": "구체적인 장애 상황과 분석 요청 사항",
  "context": "지표가 언제부터 왜 변했는지, 어떤 가설이 있는지 설명",
  "submission_requirements": "결과 컬럼(필수), 정렬, 자릿수, 날짜 형식 등 구체적 명시",
  "answer_sql": "원인을 밝혀낼 수 있는 PostgreSQL 쿼리",
  "expected_description": "어떤 결과가 나와야 원인이 증명되는지 설명",
  "expected_columns": ["col1", "col2", "..."],
  "sort_keys": ["정렬 기준 컬럼"],
  "hint": "가설 수립 힌트 (예: '먼저 채널별로 전환율을 나누어 보고, 특정 채널만 튀는지 확인해보세요')"
}}

[CRITICAL - RCA 문제의 핵심]
- 단순히 데이터를 뽑는 게 아니라, **비교 분석(Comparison)**을 유도하라.
- ❌ 나쁜 예: "오늘 탈퇴한 유저를 구하세요"
- ✅ 좋은 예: "지난주와 이번주 채널별 탈퇴율을 비교하여, 유독 탈퇴율이 치솟은 채널과 그 원인(이벤트 로그)을 파악하세요"

[데이터 스키마 - answer_sql 작성 시 반드시 사용]
- pa_users: user_id, signup_at, country, channel
- pa_sessions: session_id, user_id, started_at, device
- pa_events: event_id, user_id, session_id, event_time, event_name
- pa_orders: order_id, user_id, order_time, amount

[출력 형식]
JSON 배열 형식으로만 출력
""".strip()
