# generator/utils.py
from __future__ import annotations
import uuid
import random
from datetime import datetime, date, timedelta

def generate_session_id() -> str:
    return str(uuid.uuid4())

def generate_ts(day_str: str) -> datetime:
    """날짜 문자열(YYYY-MM-DD)을 datetime으로 변환 (시간 포함)"""
    y, m, d = map(int, day_str.split("-"))
    # Add random hour/min/sec for more realistic data
    h = random.randint(0, 23)
    mi = random.randint(0, 59)
    s = random.randint(0, 59)
    return datetime(y, m, d, h, mi, s)

def generate_date(day_str: str) -> date:
    """날짜 문자열(YYYY-MM-DD)을 date로 변환 (시간 없음)"""
    y, m, d = map(int, day_str.split("-"))
    return date(y, m, d)

def generate_date_from_datetime(dt: datetime) -> date:
    """datetime에서 date만 추출"""
    return dt.date()
