# backend/generator/anomaly_injector.py
"""
RCA 시나리오를 위한 이상 패턴 주입 모듈

실제 데이터에 비즈니스 이상 패턴을 주입하여
사용자가 SQL로 원인을 찾을 수 있도록 합니다.
"""
from __future__ import annotations

import json
import random
from datetime import datetime, timedelta, date
from enum import Enum
from typing import Dict, List, Optional, Any

from backend.common.logging import get_logger

logger = get_logger(__name__)


class AnomalyType(Enum):
    """이상 패턴 유형"""
    CHANNEL_CONVERSION_DROP = "channel_conversion_drop"      # 채널별 전환율 급락
    DEVICE_ISSUE = "device_issue"                            # 특정 디바이스 이슈
    TIME_BASED_ANOMALY = "time_based_anomaly"               # 시간대별 이상
    COUNTRY_BEHAVIOR_CHANGE = "country_behavior_change"     # 특정 국가 행동 변화
    DATA_COLLECTION_GAP = "data_collection_gap"             # 데이터 수집 누락

    # NEW: TODO #6 Scenarios
    RETENTION_DROP = "retention_drop"                        # 리텐션 급락
    CHANNEL_EFFICIENCY_DECLINE = "channel_efficiency_decline"  # 채널 효율 저하
    SIGNUP_CONVERSION_DROP = "signup_conversion_drop"        # 가입 전환율 하락


# 산업군별 적용 가능한 이상 패턴 매핑
INDUSTRY_ANOMALY_MAP = {
    "commerce": [
        AnomalyType.CHANNEL_CONVERSION_DROP,
        AnomalyType.DEVICE_ISSUE,
        AnomalyType.TIME_BASED_ANOMALY,
        AnomalyType.RETENTION_DROP,
        AnomalyType.CHANNEL_EFFICIENCY_DECLINE,
        AnomalyType.SIGNUP_CONVERSION_DROP,
    ],
    "content": [
        AnomalyType.COUNTRY_BEHAVIOR_CHANGE,
        AnomalyType.TIME_BASED_ANOMALY,
        AnomalyType.DATA_COLLECTION_GAP,
        AnomalyType.RETENTION_DROP,
        AnomalyType.SIGNUP_CONVERSION_DROP,
    ],
    "saas": [
        AnomalyType.DATA_COLLECTION_GAP,
        AnomalyType.DEVICE_ISSUE,
        AnomalyType.CHANNEL_CONVERSION_DROP,
        AnomalyType.RETENTION_DROP,
        AnomalyType.CHANNEL_EFFICIENCY_DECLINE,
        AnomalyType.SIGNUP_CONVERSION_DROP,
    ],
    "community": [
        AnomalyType.COUNTRY_BEHAVIOR_CHANGE,
        AnomalyType.TIME_BASED_ANOMALY,
        AnomalyType.CHANNEL_CONVERSION_DROP,
        AnomalyType.RETENTION_DROP,
        AnomalyType.SIGNUP_CONVERSION_DROP,
    ],
    "fintech": [
        AnomalyType.TIME_BASED_ANOMALY,
        AnomalyType.DATA_COLLECTION_GAP,
        AnomalyType.DEVICE_ISSUE,
        AnomalyType.RETENTION_DROP,
        AnomalyType.SIGNUP_CONVERSION_DROP,
    ]
}

# 이상 패턴 설명 템플릿 (Gemini 프롬프트용)
ANOMALY_DESCRIPTIONS = {
    AnomalyType.CHANNEL_CONVERSION_DROP: {
        "ko": "{channel} 채널의 구매 전환율이 {drop_rate}% 감소했습니다.",
        "hint": "채널별로 전환율을 비교해보세요. 특정 채널에서 이상이 발생했을 수 있습니다.",
    },
    AnomalyType.DEVICE_ISSUE: {
        "ko": "{device} 디바이스에서 {event} 이벤트가 {drop_rate}% 누락되었습니다.",
        "hint": "디바이스별로 이벤트 발생 비율을 확인해보세요.",
    },
    AnomalyType.TIME_BASED_ANOMALY: {
        "ko": "{start_hour}시~{end_hour}시 시간대에 {event} 이벤트가 급감했습니다.",
        "hint": "시간대별 이벤트 추이를 분석해보세요.",
    },
    AnomalyType.COUNTRY_BEHAVIOR_CHANGE: {
        "ko": "{country} 국가 사용자들의 행동 패턴이 변화했습니다. {event} 비율이 {change_rate}% 변동.",
        "hint": "국가별로 사용자 행동을 비교 분석해보세요.",
    },
    AnomalyType.DATA_COLLECTION_GAP: {
        "ko": "{affected_date} 일자에 데이터 수집이 {gap_hours}시간 동안 중단되었습니다.",
        "hint": "시간대별 데이터 수를 확인하여 누락 구간을 찾아보세요.",
    },

    # NEW: TODO #6 Scenarios
    AnomalyType.RETENTION_DROP: {
        "ko": "{cohort_period} 가입 코호트의 Day 7 리텐션이 {drop_rate}% 감소했습니다.",
        "hint": "가입 시기별로 리텐션을 비교해보세요. 특정 기간 가입자의 재방문 패턴을 확인하세요.",
    },
    AnomalyType.CHANNEL_EFFICIENCY_DECLINE: {
        "ko": "{channel} 채널의 트래픽은 정상이지만 전환율이 {drop_rate}% 하락했습니다.",
        "hint": "채널별로 유입 수와 전환 수를 각각 비교해보세요. 어느 채널이 효율이 떨어졌나요?",
    },
    AnomalyType.SIGNUP_CONVERSION_DROP: {
        "ko": "{funnel_step} 단계에서 가입 전환율이 {drop_rate}% 급락했습니다.",
        "hint": "가입 퍼널의 각 단계별 전환율을 계산해보세요. 어느 단계에서 이탈이 증가했나요?",
    },
}


def inject_channel_conversion_drop(
    pg_cur,
    target_channel: str = None,
    drop_rate: float = 0.5,
    problem_date: date = None
) -> Dict[str, Any]:
    """
    특정 채널의 전환율을 인위적으로 낮춤

    방법: 해당 채널 사용자의 purchase 이벤트 일부를 삭제
    """
    channels = ['organic', 'paid', 'social', 'referral']
    if target_channel is None:
        target_channel = random.choice(channels)

    problem_date = problem_date or date.today()

    # 해당 채널 사용자의 purchase 이벤트 중 일부 삭제
    pg_cur.execute("""
        DELETE FROM public.pa_events
        WHERE event_id IN (
            SELECT e.event_id
            FROM public.pa_events e
            JOIN public.pa_users u ON e.user_id = u.user_id
            WHERE u.channel = %s
              AND e.event_name = 'purchase'
              AND RANDOM() < %s
        )
    """, (target_channel, drop_rate))

    deleted_count = pg_cur.rowcount
    logger.info(f"[ANOMALY] Deleted {deleted_count} purchase events from {target_channel} channel")

    # 해당 채널 주문도 일부 삭제
    pg_cur.execute("""
        DELETE FROM public.pa_orders
        WHERE order_id IN (
            SELECT o.order_id
            FROM public.pa_orders o
            JOIN public.pa_users u ON o.user_id = u.user_id
            WHERE u.channel = %s
              AND RANDOM() < %s
        )
    """, (target_channel, drop_rate))

    return {
        "type": AnomalyType.CHANNEL_CONVERSION_DROP.value,
        "params": {
            "target_channel": target_channel,
            "drop_rate": int(drop_rate * 100),
            "deleted_events": deleted_count,
        },
        "affected_scope": f"channel={target_channel}",
        "description": ANOMALY_DESCRIPTIONS[AnomalyType.CHANNEL_CONVERSION_DROP]["ko"].format(
            channel=target_channel,
            drop_rate=int(drop_rate * 100)
        ),
        "hint": ANOMALY_DESCRIPTIONS[AnomalyType.CHANNEL_CONVERSION_DROP]["hint"],
    }


def inject_device_issue(
    pg_cur,
    target_device: str = None,
    target_event: str = "purchase",
    drop_rate: float = 0.8,
    problem_date: date = None
) -> Dict[str, Any]:
    """
    특정 디바이스에서 특정 이벤트 누락 시뮬레이션

    방법: 해당 디바이스의 특정 이벤트를 대부분 삭제
    """
    devices = ['iOS', 'Android', 'Web']
    if target_device is None:
        target_device = random.choice(devices)

    problem_date = problem_date or date.today()

    # 해당 디바이스의 특정 이벤트 삭제
    pg_cur.execute("""
        DELETE FROM public.pa_events
        WHERE event_id IN (
            SELECT e.event_id
            FROM public.pa_events e
            JOIN public.pa_sessions s ON e.session_id = s.session_id
            WHERE s.device = %s
              AND e.event_name = %s
              AND RANDOM() < %s
        )
    """, (target_device, target_event, drop_rate))

    deleted_count = pg_cur.rowcount
    logger.info(f"[ANOMALY] Deleted {deleted_count} {target_event} events from {target_device}")

    return {
        "type": AnomalyType.DEVICE_ISSUE.value,
        "params": {
            "target_device": target_device,
            "target_event": target_event,
            "drop_rate": int(drop_rate * 100),
            "deleted_events": deleted_count,
        },
        "affected_scope": f"device={target_device}, event={target_event}",
        "description": ANOMALY_DESCRIPTIONS[AnomalyType.DEVICE_ISSUE]["ko"].format(
            device=target_device,
            event=target_event,
            drop_rate=int(drop_rate * 100)
        ),
        "hint": ANOMALY_DESCRIPTIONS[AnomalyType.DEVICE_ISSUE]["hint"],
    }


def inject_time_based_anomaly(
    pg_cur,
    start_hour: int = None,
    end_hour: int = None,
    target_event: str = "checkout",
    drop_rate: float = 0.9,
    problem_date: date = None
) -> Dict[str, Any]:
    """
    특정 시간대에 이벤트 급감 시뮬레이션

    방법: 해당 시간대의 이벤트를 대부분 삭제
    """
    if start_hour is None:
        start_hour = random.randint(10, 18)
    if end_hour is None:
        end_hour = min(start_hour + random.randint(2, 4), 23)

    problem_date = problem_date or date.today()

    # 해당 시간대의 이벤트 삭제
    pg_cur.execute("""
        DELETE FROM public.pa_events
        WHERE event_id IN (
            SELECT event_id
            FROM public.pa_events
            WHERE event_name = %s
              AND EXTRACT(HOUR FROM event_time) >= %s
              AND EXTRACT(HOUR FROM event_time) <= %s
              AND RANDOM() < %s
        )
    """, (target_event, start_hour, end_hour, drop_rate))

    deleted_count = pg_cur.rowcount
    logger.info(f"[ANOMALY] Deleted {deleted_count} {target_event} events during {start_hour}:00-{end_hour}:00")

    return {
        "type": AnomalyType.TIME_BASED_ANOMALY.value,
        "params": {
            "start_hour": start_hour,
            "end_hour": end_hour,
            "target_event": target_event,
            "drop_rate": int(drop_rate * 100),
            "deleted_events": deleted_count,
        },
        "affected_scope": f"hour={start_hour}-{end_hour}, event={target_event}",
        "description": ANOMALY_DESCRIPTIONS[AnomalyType.TIME_BASED_ANOMALY]["ko"].format(
            start_hour=start_hour,
            end_hour=end_hour,
            event=target_event
        ),
        "hint": ANOMALY_DESCRIPTIONS[AnomalyType.TIME_BASED_ANOMALY]["hint"],
    }


def inject_country_behavior_change(
    pg_cur,
    target_country: str = None,
    target_event: str = "purchase",
    change_rate: float = -0.6,
    problem_date: date = None
) -> Dict[str, Any]:
    """
    특정 국가 사용자들의 행동 패턴 변화

    방법: 해당 국가 사용자의 특정 이벤트 비율 조정
    """
    countries = ['KR', 'US', 'JP', 'UK']
    if target_country is None:
        target_country = random.choice(countries)

    problem_date = problem_date or date.today()
    drop_rate = abs(change_rate)

    # 해당 국가 사용자의 이벤트 삭제
    pg_cur.execute("""
        DELETE FROM public.pa_events
        WHERE event_id IN (
            SELECT e.event_id
            FROM public.pa_events e
            JOIN public.pa_users u ON e.user_id = u.user_id
            WHERE u.country = %s
              AND e.event_name = %s
              AND RANDOM() < %s
        )
    """, (target_country, target_event, drop_rate))

    deleted_count = pg_cur.rowcount
    logger.info(f"[ANOMALY] Modified {deleted_count} events for {target_country} country")

    return {
        "type": AnomalyType.COUNTRY_BEHAVIOR_CHANGE.value,
        "params": {
            "target_country": target_country,
            "target_event": target_event,
            "change_rate": int(change_rate * 100),
            "deleted_events": deleted_count,
        },
        "affected_scope": f"country={target_country}, event={target_event}",
        "description": ANOMALY_DESCRIPTIONS[AnomalyType.COUNTRY_BEHAVIOR_CHANGE]["ko"].format(
            country=target_country,
            event=target_event,
            change_rate=int(change_rate * 100)
        ),
        "hint": ANOMALY_DESCRIPTIONS[AnomalyType.COUNTRY_BEHAVIOR_CHANGE]["hint"],
    }


def inject_data_collection_gap(
    pg_cur,
    gap_hours: int = None,
    gap_start_hour: int = None,
    problem_date: date = None
) -> Dict[str, Any]:
    """
    데이터 수집 누락 시뮬레이션

    방법: 특정 시간대의 모든 이벤트 삭제
    """
    if gap_hours is None:
        gap_hours = random.randint(2, 6)
    if gap_start_hour is None:
        gap_start_hour = random.randint(8, 20 - gap_hours)

    gap_end_hour = gap_start_hour + gap_hours
    problem_date = problem_date or date.today()

    # 해당 시간대의 모든 이벤트 삭제
    pg_cur.execute("""
        DELETE FROM public.pa_events
        WHERE EXTRACT(HOUR FROM event_time) >= %s
          AND EXTRACT(HOUR FROM event_time) < %s
    """, (gap_start_hour, gap_end_hour))

    deleted_count = pg_cur.rowcount
    logger.info(f"[ANOMALY] Deleted {deleted_count} events during collection gap {gap_start_hour}:00-{gap_end_hour}:00")

    return {
        "type": AnomalyType.DATA_COLLECTION_GAP.value,
        "params": {
            "gap_start_hour": gap_start_hour,
            "gap_end_hour": gap_end_hour,
            "gap_hours": gap_hours,
            "deleted_events": deleted_count,
        },
        "affected_scope": f"hour={gap_start_hour}-{gap_end_hour}",
        "description": ANOMALY_DESCRIPTIONS[AnomalyType.DATA_COLLECTION_GAP]["ko"].format(
            affected_date=str(problem_date),
            gap_hours=gap_hours
        ),
        "hint": ANOMALY_DESCRIPTIONS[AnomalyType.DATA_COLLECTION_GAP]["hint"],
    }


# NEW: TODO #6 Anomaly Injection Functions

def inject_retention_drop(
    pg_cur,
    cohort_days_ago: int = None,
    drop_rate: float = 0.6,
    problem_date: date = None
) -> Dict[str, Any]:
    """
    특정 가입 코호트의 리텐션(재방문) 급락 시뮬레이션

    방법: 특정 기간에 가입한 유저의 재방문 세션을 삭제하여 D7 리텐션 하락 효과
    """
    if cohort_days_ago is None:
        cohort_days_ago = random.randint(7, 14)

    problem_date = problem_date or date.today()
    cohort_start = problem_date - timedelta(days=cohort_days_ago)
    cohort_end = cohort_start + timedelta(days=1)

    # 해당 기간에 가입한 유저의 재방문 세션 삭제
    pg_cur.execute("""
        DELETE FROM public.pa_sessions
        WHERE session_id IN (
            SELECT s.session_id
            FROM public.pa_sessions s
            JOIN public.pa_users u ON s.user_id = u.user_id
            WHERE u.signup_at >= %s
              AND u.signup_at < %s
              AND s.started_at > u.signup_at + INTERVAL '1 day'
              AND RANDOM() < %s
        )
    """, (cohort_start, cohort_end, drop_rate))

    deleted_sessions = pg_cur.rowcount

    # 삭제된 세션의 이벤트도 제거
    pg_cur.execute("""
        DELETE FROM public.pa_events
        WHERE session_id NOT IN (SELECT session_id FROM public.pa_sessions)
    """)

    deleted_events = pg_cur.rowcount
    logger.info(f"[ANOMALY] Deleted {deleted_sessions} return sessions and {deleted_events} events for cohort {cohort_days_ago} days ago")

    return {
        "type": AnomalyType.RETENTION_DROP.value,
        "params": {
            "cohort_days_ago": cohort_days_ago,
            "drop_rate": int(drop_rate * 100),
            "deleted_sessions": deleted_sessions,
            "deleted_events": deleted_events,
        },
        "affected_scope": f"cohort={cohort_days_ago}일전 가입자",
        "description": ANOMALY_DESCRIPTIONS[AnomalyType.RETENTION_DROP]["ko"].format(
            cohort_period=f"{cohort_days_ago}일전",
            drop_rate=int(drop_rate * 100)
        ),
        "hint": ANOMALY_DESCRIPTIONS[AnomalyType.RETENTION_DROP]["hint"],
        "hints": [
            "리텐션 지표가 비정상적입니다. 이번 주와 지난 주를 비교해보세요.",
            f"{cohort_days_ago-7}~{cohort_days_ago+7}일 전에 가입한 유저들에게 무슨 일이 있었는지 확인하세요.",
            "가입 코호트별로 재방문 세션 비율을 계산해보세요. 어느 코호트가 떨어졌나요?"
        ],
        "root_cause": f"{cohort_days_ago}일 전 가입 코호트의 재방문 세션 급감",
    }


def inject_channel_efficiency_decline(
    pg_cur,
    target_channel: str = None,
    drop_rate: float = 0.5,
    problem_date: date = None
) -> Dict[str, Any]:
    """
    특정 채널의 전환 효율 저하 시뮬레이션

    방법: 트래픽(세션)은 유지하되, 구매 전환만 감소시킴
    """
    channels = ['organic', 'paid', 'social', 'referral']
    if target_channel is None:
        target_channel = random.choice(channels)

    problem_date = problem_date or date.today()

    # 해당 채널 사용자의 구매 전환 이벤트만 삭제 (세션은 유지)
    pg_cur.execute("""
        DELETE FROM public.pa_orders
        WHERE order_id IN (
            SELECT o.order_id
            FROM public.pa_orders o
            JOIN public.pa_users u ON o.user_id = u.user_id
            WHERE u.channel = %s
              AND RANDOM() < %s
        )
    """, (target_channel, drop_rate))

    deleted_orders = pg_cur.rowcount

    # 구매 이벤트도 삭제
    pg_cur.execute("""
        DELETE FROM public.pa_events
        WHERE event_id IN (
            SELECT e.event_id
            FROM public.pa_events e
            JOIN public.pa_users u ON e.user_id = u.user_id
            WHERE u.channel = %s
              AND e.event_name = 'purchase'
              AND RANDOM() < %s
        )
    """, (target_channel, drop_rate))

    deleted_events = pg_cur.rowcount
    logger.info(f"[ANOMALY] Deleted {deleted_orders} orders and {deleted_events} purchase events from {target_channel} channel")

    return {
        "type": AnomalyType.CHANNEL_EFFICIENCY_DECLINE.value,
        "params": {
            "target_channel": target_channel,
            "drop_rate": int(drop_rate * 100),
            "deleted_orders": deleted_orders,
            "deleted_events": deleted_events,
        },
        "affected_scope": f"channel={target_channel}",
        "description": ANOMALY_DESCRIPTIONS[AnomalyType.CHANNEL_EFFICIENCY_DECLINE]["ko"].format(
            channel=target_channel,
            drop_rate=int(drop_rate * 100)
        ),
        "hint": ANOMALY_DESCRIPTIONS[AnomalyType.CHANNEL_EFFICIENCY_DECLINE]["hint"],
        "hints": [
            "전체 트래픽은 정상으로 보이지만, 전환에 문제가 있는 것 같습니다.",
            "유입 채널별로 전환율을 나누어 분석해보세요.",
            f"{target_channel} 채널의 전환율을 다른 채널과 비교해보세요. 무엇이 다른가요?"
        ],
        "root_cause": f"{target_channel} 채널의 전환 효율 저하 (트래픽 유지, 전환 감소)",
    }


def inject_signup_conversion_drop(
    pg_cur,
    funnel_step: str = None,
    drop_rate: float = 0.6,
    problem_date: date = None
) -> Dict[str, Any]:
    """
    가입 퍼널 특정 단계에서 전환율 급락 시뮬레이션

    방법: 특정 퍼널 단계 이벤트를 삭제하여 이탈 증가
    """
    funnel_steps = ['signup_start', 'signup_email', 'signup_verify', 'signup_complete']
    if funnel_step is None:
        funnel_step = random.choice(funnel_steps[1:])  # signup_start 제외

    problem_date = problem_date or date.today()

    # 해당 퍼널 단계 이벤트 삭제
    pg_cur.execute("""
        DELETE FROM public.pa_events
        WHERE event_id IN (
            SELECT event_id
            FROM public.pa_events
            WHERE event_name = %s
              AND RANDOM() < %s
        )
    """, (funnel_step, drop_rate))

    deleted_events = pg_cur.rowcount

    # 해당 단계에서 이탈한 유저는 완료 이벤트도 없어야 함
    if funnel_step != 'signup_complete':
        pg_cur.execute("""
            DELETE FROM public.pa_users
            WHERE user_id IN (
                SELECT u.user_id
                FROM public.pa_users u
                LEFT JOIN public.pa_events e ON u.user_id = e.user_id AND e.event_name = %s
                WHERE e.event_id IS NULL
                  AND RANDOM() < %s
                LIMIT 100
            )
        """, (funnel_step, drop_rate * 0.5))

        deleted_users = pg_cur.rowcount
    else:
        deleted_users = 0

    logger.info(f"[ANOMALY] Deleted {deleted_events} {funnel_step} events and {deleted_users} incomplete signups")

    return {
        "type": AnomalyType.SIGNUP_CONVERSION_DROP.value,
        "params": {
            "funnel_step": funnel_step,
            "drop_rate": int(drop_rate * 100),
            "deleted_events": deleted_events,
            "deleted_users": deleted_users,
        },
        "affected_scope": f"funnel_step={funnel_step}",
        "description": ANOMALY_DESCRIPTIONS[AnomalyType.SIGNUP_CONVERSION_DROP]["ko"].format(
            funnel_step=funnel_step,
            drop_rate=int(drop_rate * 100)
        ),
        "hint": ANOMALY_DESCRIPTIONS[AnomalyType.SIGNUP_CONVERSION_DROP]["hint"],
        "hints": [
            "가입 수가 감소하고 있습니다. 퍼널 분석으로 병목 지점을 찾아보세요.",
            "각 단계별 전환율을 비교해보세요. 유저가 어디서 이탈하나요?",
            f"{funnel_step} 단계에서 비정상적인 이탈이 발생합니다. 시간대와 디바이스를 조사하세요."
        ],
        "root_cause": f"가입 퍼널 {funnel_step} 단계에서 전환율 급락",
    }


# 이상 패턴 주입 함수 매핑
ANOMALY_INJECTORS = {
    AnomalyType.CHANNEL_CONVERSION_DROP: inject_channel_conversion_drop,
    AnomalyType.DEVICE_ISSUE: inject_device_issue,
    AnomalyType.TIME_BASED_ANOMALY: inject_time_based_anomaly,
    AnomalyType.COUNTRY_BEHAVIOR_CHANGE: inject_country_behavior_change,
    AnomalyType.DATA_COLLECTION_GAP: inject_data_collection_gap,
    # NEW: TODO #6 Scenarios
    AnomalyType.RETENTION_DROP: inject_retention_drop,
    AnomalyType.CHANNEL_EFFICIENCY_DECLINE: inject_channel_efficiency_decline,
    AnomalyType.SIGNUP_CONVERSION_DROP: inject_signup_conversion_drop,
}


def inject_random_anomaly(
    pg_cur,
    product_type: str = "commerce",
    problem_date: date = None
) -> Dict[str, Any]:
    """
    산업군에 맞는 랜덤 이상 패턴 선택 및 주입

    Args:
        pg_cur: PostgreSQL 커서
        product_type: 산업군 (commerce, content, saas, community, fintech)
        problem_date: 문제 날짜

    Returns:
        주입된 이상 패턴 메타데이터
    """
    problem_date = problem_date or date.today()

    # 산업군에 맞는 이상 패턴 선택
    available_anomalies = INDUSTRY_ANOMALY_MAP.get(product_type, INDUSTRY_ANOMALY_MAP["commerce"])
    selected_anomaly = random.choice(available_anomalies)

    logger.info(f"[ANOMALY] Selected anomaly type: {selected_anomaly.value} for {product_type}")

    # 이상 패턴 주입
    injector = ANOMALY_INJECTORS[selected_anomaly]
    metadata = injector(pg_cur, problem_date=problem_date)

    # 메타데이터에 추가 정보
    metadata["product_type"] = product_type
    metadata["problem_date"] = str(problem_date)

    return metadata


def save_anomaly_metadata(pg_cur, metadata: Dict[str, Any]) -> int:
    """
    주입된 이상 패턴 메타데이터를 DB에 저장

    Returns:
        저장된 레코드 ID
    """
    hints = metadata.get("hints", [])
    if isinstance(hints, str):
        hints = [hints]  # 단일 힌트를 배열로 변환

    pg_cur.execute("""
        INSERT INTO public.rca_anomaly_metadata
        (problem_date, product_type, anomaly_type, anomaly_params, affected_scope, description, hints, root_cause)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (
        metadata.get("problem_date"),
        metadata.get("product_type"),
        metadata.get("type"),
        json.dumps(metadata.get("params", {})),
        metadata.get("affected_scope"),
        metadata.get("description"),
        json.dumps(hints),
        metadata.get("root_cause"),
    ))

    record_id = pg_cur.fetchone()[0]
    logger.info(f"[ANOMALY] Saved anomaly metadata with id={record_id}, hints={len(hints)}")

    return record_id


def get_latest_anomaly_metadata(pg_cur, problem_date: date = None) -> Optional[Dict[str, Any]]:
    """
    최근 주입된 이상 패턴 메타데이터 조회
    """
    problem_date = problem_date or date.today()

    pg_cur.execute("""
        SELECT id, product_type, anomaly_type, anomaly_params, affected_scope, description
        FROM public.rca_anomaly_metadata
        WHERE problem_date = %s
        ORDER BY created_at DESC
        LIMIT 1
    """, (problem_date,))

    row = pg_cur.fetchone()
    if not row:
        return None

    return {
        "id": row[0],
        "product_type": row[1],
        "type": row[2],
        "params": row[3] if isinstance(row[3], dict) else json.loads(row[3] or "{}"),
        "affected_scope": row[4],
        "description": row[5],
    }
