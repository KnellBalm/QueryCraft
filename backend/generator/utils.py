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
    # Add random hour/min/sec for more realistic data
    h = random.randint(0, 23)
    mi = random.randint(0, 59)
    s = random.randint(0, 59)
    return datetime(y, m, d, h, mi, s)
