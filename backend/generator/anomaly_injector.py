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


# 산업군별 적용 가능한 이상 패턴 매핑
INDUSTRY_ANOMALY_MAP = {
    "commerce": [
        AnomalyType.CHANNEL_CONVERSION_DROP,
        AnomalyType.DEVICE_ISSUE,
        AnomalyType.TIME_BASED_ANOMALY,
    ],
    "content": [
        AnomalyType.COUNTRY_BEHAVIOR_CHANGE,
        AnomalyType.TIME_BASED_ANOMALY,
        AnomalyType.DATA_COLLECTION_GAP,
    ],
    "saas": [
        AnomalyType.DATA_COLLECTION_GAP,
        AnomalyType.DEVICE_ISSUE,
        AnomalyType.CHANNEL_CONVERSION_DROP,
    ],
    "community": [
        AnomalyType.COUNTRY_BEHAVIOR_CHANGE,
        AnomalyType.TIME_BASED_ANOMALY,
        AnomalyType.CHANNEL_CONVERSION_DROP,
    ],
    "fintech": [
        AnomalyType.TIME_BASED_ANOMALY,
        AnomalyType.DATA_COLLECTION_GAP,
        AnomalyType.DEVICE_ISSUE,
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


# 이상 패턴 주입 함수 매핑
ANOMALY_INJECTORS = {
    AnomalyType.CHANNEL_CONVERSION_DROP: inject_channel_conversion_drop,
    AnomalyType.DEVICE_ISSUE: inject_device_issue,
    AnomalyType.TIME_BASED_ANOMALY: inject_time_based_anomaly,
    AnomalyType.COUNTRY_BEHAVIOR_CHANGE: inject_country_behavior_change,
    AnomalyType.DATA_COLLECTION_GAP: inject_data_collection_gap,
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
    pg_cur.execute("""
        INSERT INTO public.rca_anomaly_metadata
        (problem_date, product_type, anomaly_type, anomaly_params, affected_scope, description)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (
        metadata.get("problem_date"),
        metadata.get("product_type"),
        metadata.get("type"),
        json.dumps(metadata.get("params", {})),
        metadata.get("affected_scope"),
        metadata.get("description"),
    ))

    record_id = pg_cur.fetchone()[0]
    logger.info(f"[ANOMALY] Saved anomaly metadata with id={record_id}")

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
