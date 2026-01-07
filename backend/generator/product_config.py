# generator/product_config.py
"""
Product Type별 이벤트 정의 및 확률 설정
모든 하드코딩된 이벤트는 이 파일에서 관리
"""
from __future__ import annotations

import os
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv

load_dotenv()

# =====================================================
# Product Type 기본 설정
# =====================================================

# 지원하는 Product Types
PRODUCT_TYPES = os.getenv("PRODUCT_TYPES", "commerce,content,saas,community,fintech").split(",")

# Product Type 분포 (없으면 균등 분포)
_dist_str = os.getenv("PRODUCT_TYPE_DISTRIBUTION", "")
PRODUCT_TYPE_DISTRIBUTION: Dict[str, float] = {}
if _dist_str:
    for item in _dist_str.split(","):
        if ":" in item:
            ptype, prob = item.split(":")
            PRODUCT_TYPE_DISTRIBUTION[ptype.strip()] = float(prob)
else:
    # 기본 균등 분포
    for ptype in PRODUCT_TYPES:
        PRODUCT_TYPE_DISTRIBUTION[ptype] = 1.0 / len(PRODUCT_TYPES)


def select_product_type() -> str:
    """확률에 따라 Product Type 선택"""
    types = list(PRODUCT_TYPE_DISTRIBUTION.keys())
    weights = list(PRODUCT_TYPE_DISTRIBUTION.values())
    return random.choices(types, weights=weights, k=1)[0]


# =====================================================
# Commerce Events (15개)
# =====================================================
COMMERCE_EVENTS = [
    "page_view",
    "search",
    "view_product",
    "view_review",
    "add_to_cart",
    "remove_from_cart",
    "apply_coupon",
    "begin_checkout",
    "purchase",
    "refund_request",
    "wishlist_add",
    "notification_open",
    "compare_product",
    "bundle_view",
    "reorder",
]

COMMERCE_PROBABILITIES = {
    "page_view": 1.0,           # 모든 세션
    "search": float(os.getenv("COMMERCE_PROB_SEARCH", "0.45")),
    "view_product": float(os.getenv("COMMERCE_PROB_VIEW_PRODUCT", "0.70")),
    "view_review": float(os.getenv("COMMERCE_PROB_VIEW_REVIEW", "0.35")),
    "add_to_cart": float(os.getenv("COMMERCE_PROB_ADD_TO_CART", "0.25")),
    "remove_from_cart": float(os.getenv("COMMERCE_PROB_REMOVE_FROM_CART", "0.08")),
    "apply_coupon": float(os.getenv("COMMERCE_PROB_APPLY_COUPON", "0.12")),
    "begin_checkout": float(os.getenv("COMMERCE_PROB_BEGIN_CHECKOUT", "0.18")),
    "purchase": float(os.getenv("COMMERCE_PROB_PURCHASE", "0.08")),
    "refund_request": float(os.getenv("COMMERCE_PROB_REFUND_REQUEST", "0.02")),
    "wishlist_add": float(os.getenv("COMMERCE_PROB_WISHLIST_ADD", "0.15")),
    "notification_open": float(os.getenv("COMMERCE_PROB_NOTIFICATION_OPEN", "0.20")),
    "compare_product": float(os.getenv("COMMERCE_PROB_COMPARE_PRODUCT", "0.10")),
    "bundle_view": float(os.getenv("COMMERCE_PROB_BUNDLE_VIEW", "0.08")),
    "reorder": float(os.getenv("COMMERCE_PROB_REORDER", "0.05")),
}

# Commerce Funnel Flow (순서 제약)
COMMERCE_FUNNEL = [
    "page_view",
    "search",
    "view_product",
    "view_review",
    "add_to_cart",
    "apply_coupon",
    "begin_checkout",
    "purchase",
]


# =====================================================
# Content Events (12개)
# =====================================================
CONTENT_EVENTS = [
    "page_view",
    "read_content",
    "scroll_25",
    "scroll_50",
    "scroll_75",
    "scroll_100",
    "like",
    "comment",
    "share",
    "subscribe",
    "unsubscribe",
    "bookmark",
]

CONTENT_PROBABILITIES = {
    "page_view": 1.0,
    "read_content": float(os.getenv("CONTENT_PROB_READ_CONTENT", "0.85")),
    "scroll_25": float(os.getenv("CONTENT_PROB_SCROLL_25", "0.70")),
    "scroll_50": float(os.getenv("CONTENT_PROB_SCROLL_50", "0.50")),
    "scroll_75": float(os.getenv("CONTENT_PROB_SCROLL_75", "0.35")),
    "scroll_100": float(os.getenv("CONTENT_PROB_SCROLL_100", "0.20")),
    "like": float(os.getenv("CONTENT_PROB_LIKE", "0.15")),
    "comment": float(os.getenv("CONTENT_PROB_COMMENT", "0.05")),
    "share": float(os.getenv("CONTENT_PROB_SHARE", "0.08")),
    "subscribe": float(os.getenv("CONTENT_PROB_SUBSCRIBE", "0.04")),
    "unsubscribe": float(os.getenv("CONTENT_PROB_UNSUBSCRIBE", "0.01")),
    "bookmark": float(os.getenv("CONTENT_PROB_BOOKMARK", "0.12")),
}

CONTENT_ENGAGEMENT_FLOW = [
    "page_view",
    "read_content",
    "scroll_25",
    "scroll_50",
    "scroll_75",
    "scroll_100",
]


# =====================================================
# SaaS Events (13개)
# =====================================================
SAAS_EVENTS = [
    "login",
    "logout",
    "dashboard_view",
    "feature_use",
    "create_project",
    "invite_member",
    "export_data",
    "api_call",
    "upgrade_plan",
    "downgrade_plan",
    "cancel_subscription",
    "support_ticket",
    "onboarding_complete",
]

SAAS_PROBABILITIES = {
    "login": 1.0,
    "logout": float(os.getenv("SAAS_PROB_LOGOUT", "0.90")),
    "dashboard_view": float(os.getenv("SAAS_PROB_DASHBOARD_VIEW", "0.95")),
    "feature_use": float(os.getenv("SAAS_PROB_FEATURE_USE", "0.75")),
    "create_project": float(os.getenv("SAAS_PROB_CREATE_PROJECT", "0.20")),
    "invite_member": float(os.getenv("SAAS_PROB_INVITE_MEMBER", "0.08")),
    "export_data": float(os.getenv("SAAS_PROB_EXPORT_DATA", "0.15")),
    "api_call": float(os.getenv("SAAS_PROB_API_CALL", "0.25")),
    "upgrade_plan": float(os.getenv("SAAS_PROB_UPGRADE_PLAN", "0.03")),
    "downgrade_plan": float(os.getenv("SAAS_PROB_DOWNGRADE_PLAN", "0.01")),
    "cancel_subscription": float(os.getenv("SAAS_PROB_CANCEL_SUBSCRIPTION", "0.005")),
    "support_ticket": float(os.getenv("SAAS_PROB_SUPPORT_TICKET", "0.05")),
    "onboarding_complete": float(os.getenv("SAAS_PROB_ONBOARDING_COMPLETE", "0.40")),
}

SAAS_ACTIVATION_FLOW = [
    "login",
    "dashboard_view",
    "onboarding_complete",
    "feature_use",
    "create_project",
]


# =====================================================
# Community Events (11개)
# =====================================================
COMMUNITY_EVENTS = [
    "view_feed",
    "post_create",
    "post_edit",
    "comment",
    "reply",
    "like",
    "report",
    "follow",
    "unfollow",
    "message_send",
    "profile_view",
]

COMMUNITY_PROBABILITIES = {
    "view_feed": 1.0,
    "post_create": float(os.getenv("COMMUNITY_PROB_POST_CREATE", "0.08")),
    "post_edit": float(os.getenv("COMMUNITY_PROB_POST_EDIT", "0.02")),
    "comment": float(os.getenv("COMMUNITY_PROB_COMMENT", "0.15")),
    "reply": float(os.getenv("COMMUNITY_PROB_REPLY", "0.10")),
    "like": float(os.getenv("COMMUNITY_PROB_LIKE", "0.35")),
    "report": float(os.getenv("COMMUNITY_PROB_REPORT", "0.01")),
    "follow": float(os.getenv("COMMUNITY_PROB_FOLLOW", "0.12")),
    "unfollow": float(os.getenv("COMMUNITY_PROB_UNFOLLOW", "0.03")),
    "message_send": float(os.getenv("COMMUNITY_PROB_MESSAGE_SEND", "0.08")),
    "profile_view": float(os.getenv("COMMUNITY_PROB_PROFILE_VIEW", "0.25")),
}

COMMUNITY_ENGAGEMENT_FLOW = [
    "view_feed",
    "profile_view",
    "follow",
    "like",
    "comment",
    "post_create",
]


# =====================================================
# Fintech Events (12개)
# =====================================================
FINTECH_EVENTS = [
    "login",
    "account_view",
    "balance_check",
    "transfer_attempt",
    "transfer_success",
    "transfer_fail",
    "card_payment",
    "chargeback",
    "fraud_alert_view",
    "kyc_submit",
    "loan_apply",
    "investment_view",
]

FINTECH_PROBABILITIES = {
    "login": 1.0,
    "account_view": float(os.getenv("FINTECH_PROB_ACCOUNT_VIEW", "0.95")),
    "balance_check": float(os.getenv("FINTECH_PROB_BALANCE_CHECK", "0.80")),
    "transfer_attempt": float(os.getenv("FINTECH_PROB_TRANSFER_ATTEMPT", "0.30")),
    "transfer_success": float(os.getenv("FINTECH_PROB_TRANSFER_SUCCESS", "0.25")),
    "transfer_fail": float(os.getenv("FINTECH_PROB_TRANSFER_FAIL", "0.05")),
    "card_payment": float(os.getenv("FINTECH_PROB_CARD_PAYMENT", "0.20")),
    "chargeback": float(os.getenv("FINTECH_PROB_CHARGEBACK", "0.01")),
    "fraud_alert_view": float(os.getenv("FINTECH_PROB_FRAUD_ALERT_VIEW", "0.02")),
    "kyc_submit": float(os.getenv("FINTECH_PROB_KYC_SUBMIT", "0.15")),
    "loan_apply": float(os.getenv("FINTECH_PROB_LOAN_APPLY", "0.05")),
    "investment_view": float(os.getenv("FINTECH_PROB_INVESTMENT_VIEW", "0.18")),
}

FINTECH_TRANSACTION_FLOW = [
    "login",
    "account_view",
    "balance_check",
    "transfer_attempt",
    "transfer_success",
]


# =====================================================
# Product Type별 KPI 정의
# =====================================================
PRODUCT_KPI_GUIDE = {
    "commerce": {
        "north_star": "GMV (Gross Merchandise Value)",
        "activation_event": "purchase",
        "activation_criteria": "첫 구매 완료",
        "retention_events": ["page_view", "purchase"],
        "retention_period_days": 30,
        "key_metrics": [
            "DAU/MAU",
            "Conversion Rate (view → purchase)",
            "Cart Abandonment Rate",
            "Average Order Value",
            "Customer Lifetime Value",
            "Coupon Redemption Rate",
        ],
        "common_mistakes": [
            "모든 페이지뷰를 동일하게 카운트",
            "cart abandonment를 단순 비율로만 측정",
            "재구매와 신규구매 미구분",
        ]
    },
    "content": {
        "north_star": "Total Reading Time",
        "activation_event": "scroll_100",
        "activation_criteria": "콘텐츠 완독 1회 이상",
        "retention_events": ["read_content", "scroll_50"],
        "retention_period_days": 7,
        "key_metrics": [
            "DAU",
            "Average Reading Depth (scroll %)",
            "Content Completion Rate",
            "Share Rate",
            "Subscription Conversion",
            "Churn Rate",
        ],
        "common_mistakes": [
            "페이지뷰만으로 engagement 측정",
            "scroll depth 무시",
            "heavy user와 casual reader 미구분",
        ]
    },
    "saas": {
        "north_star": "Weekly Active Users (feature_use 기준)",
        "activation_event": "onboarding_complete",
        "activation_criteria": "온보딩 완료 + feature_use 3회 이상",
        "retention_events": ["login", "feature_use"],
        "retention_period_days": 7,
        "key_metrics": [
            "WAU",
            "Feature Adoption Rate",
            "Time to Value",
            "Upgrade Rate",
            "Churn Rate",
            "NPS (Net Promoter Score)",
        ],
        "common_mistakes": [
            "login만으로 active 정의",
            "모든 feature를 동일 가중치로 측정",
            "trial user와 paid user 미구분",
        ]
    },
    "community": {
        "north_star": "Daily Active Creators",
        "activation_event": "post_create",
        "activation_criteria": "첫 포스트 작성",
        "retention_events": ["view_feed", "post_create", "comment"],
        "retention_period_days": 7,
        "key_metrics": [
            "DAU",
            "Creator/Consumer Ratio",
            "Engagement Rate (like + comment) / view",
            "Viral Coefficient",
            "Average Session Duration",
        ],
        "common_mistakes": [
            "lurker를 inactive로 분류",
            "팔로워 수만으로 영향력 측정",
            "spam/bot 미제외",
        ]
    },
    "fintech": {
        "north_star": "Monthly Transaction Volume",
        "activation_event": "transfer_success",
        "activation_criteria": "첫 송금 성공",
        "retention_events": ["login", "transfer_success", "card_payment"],
        "retention_period_days": 30,
        "key_metrics": [
            "MAU",
            "Transaction Success Rate",
            "Average Transaction Value",
            "Fraud Detection Rate",
            "KYC Completion Rate",
            "Cross-sell Rate (loan, investment)",
        ],
        "common_mistakes": [
            "실패 트랜잭션 무시",
            "사기 탐지 오탐 미측정",
            "고액/소액 트랜잭션 동일 가중치",
        ]
    },
}


# =====================================================
# 헬퍼 함수
# =====================================================
def get_events_for_type(product_type: str) -> List[str]:
    """Product Type에 맞는 이벤트 목록 반환"""
    event_map = {
        "commerce": COMMERCE_EVENTS,
        "content": CONTENT_EVENTS,
        "saas": SAAS_EVENTS,
        "community": COMMUNITY_EVENTS,
        "fintech": FINTECH_EVENTS,
    }
    return event_map.get(product_type, COMMERCE_EVENTS)


def get_probabilities_for_type(product_type: str) -> Dict[str, float]:
    """Product Type에 맞는 확률 반환"""
    prob_map = {
        "commerce": COMMERCE_PROBABILITIES,
        "content": CONTENT_PROBABILITIES,
        "saas": SAAS_PROBABILITIES,
        "community": COMMUNITY_PROBABILITIES,
        "fintech": FINTECH_PROBABILITIES,
    }
    return prob_map.get(product_type, COMMERCE_PROBABILITIES)


def get_flow_for_type(product_type: str) -> List[str]:
    """Product Type에 맞는 주요 플로우 반환"""
    flow_map = {
        "commerce": COMMERCE_FUNNEL,
        "content": CONTENT_ENGAGEMENT_FLOW,
        "saas": SAAS_ACTIVATION_FLOW,
        "community": COMMUNITY_ENGAGEMENT_FLOW,
        "fintech": FINTECH_TRANSACTION_FLOW,
    }
    return flow_map.get(product_type, COMMERCE_FUNNEL)


def get_kpi_guide(product_type: str) -> dict:
    """Product Type에 맞는 KPI 가이드 반환"""
    return PRODUCT_KPI_GUIDE.get(product_type, PRODUCT_KPI_GUIDE["commerce"])
