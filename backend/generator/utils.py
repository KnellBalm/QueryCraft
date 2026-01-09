# generator/utils.py
from __future__ import annotations
import uuid
import random
from datetime import datetime, date, timedelta

def generate_session_id() -> str:
    return str(uuid.uuid4())

def generate_ts(day_str: str) -> date:
    # day_str = "YYYY-MM-DD"
    y, m, d = map(int, day_str.split("-"))
    return date(y, m, d)
