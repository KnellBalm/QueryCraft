# generator/utils.py
from __future__ import annotations
import uuid
import random
from datetime import datetime, date, timedelta

def generate_session_id() -> str:
    return str(uuid.uuid4())

def generate_ts(day_str: str) -> datetime:
    # day_str = "YYYY-MM-DD"
    y, m, d = map(int, day_str.split("-"))
    base = datetime(y, m, d, 0, 0, 0)
    # 하루 내 랜덤 시간
    return base + timedelta(seconds=random.randint(0, 86399))
