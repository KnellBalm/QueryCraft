# generator/config.py
from __future__ import annotations
import os
import random
from dataclasses import dataclass
from datetime import date, timedelta
from dotenv import load_dotenv

load_dotenv()

def _env_list(key: str, default: str) -> list[str]:
    v = os.getenv(key, default)
    return [x.strip() for x in v.split(",") if x.strip()]

def _env_int(key: str, default: int) -> int:
    return int(os.getenv(key, str(default)))

def _env_float(key: str, default: float) -> float:
    return float(os.getenv(key, str(default)))

def _env_str(key: str, default: str) -> str:
    return os.getenv(key, default)

# ===== Generator 제어 =====
GENERATOR_TARGETS = _env_list("GENERATOR_TARGETS", "postgres,duckdb")  # postgres | duckdb | 둘다
GENERATOR_MODES = _env_list("GENERATOR_MODES", "stream,pa")           # stream | pa | 둘다

# ===== 재현성 =====
GEN_SEED_MODE = _env_str("GEN_SEED_MODE", "date")  # date | fixed | none
GEN_SEED_FIXED = _env_int("GEN_SEED_FIXED", 12345)

# ------------------------------
# Stream 기간 설정 (자동)
# ------------------------------
STREAM_TOTAL_DAYS_MIN = _env_int("STREAM_TOTAL_DAYS_MIN", 180)
STREAM_TOTAL_DAYS_MAX = _env_int("STREAM_TOTAL_DAYS_MAX", 220)

TODAY = date.today()
TOTAL_DAYS = random.randint(STREAM_TOTAL_DAYS_MIN, STREAM_TOTAL_DAYS_MAX)
STREAM_START_DATE = TODAY - timedelta(days=TOTAL_DAYS)
STREAM_END_DATE = TODAY

# ------------------------------
# Stream User 설정
# ------------------------------
STREAM_N_USERS = _env_int("STREAM_N_USERS", 5_000)  # 증분 생성용
STREAM_DAILY_EVENTS = _env_int("STREAM_DAILY_EVENTS", 10_000)  # 매일 1만 row
STREAM_RETENTION_DAYS = _env_int("STREAM_RETENTION_DAYS", 7)  # 7일 보관
STREAM_NEW_USERS_DAILY = (
    _env_int("STREAM_NEW_USERS_DAILY_MIN", 50),
    _env_int("STREAM_NEW_USERS_DAILY_MAX", 300),
)

# ------------------------------
# Stream 이벤트 확률
# ------------------------------
STREAM_PROB_VISIT = 1.0
STREAM_PROB_VIEW = _env_float("STREAM_PROB_VIEW", 0.9)
STREAM_PROB_CART = _env_float("STREAM_PROB_CART", 0.3)
STREAM_PROB_CHECKOUT = _env_float("STREAM_PROB_CHECKOUT", 0.18)
STREAM_PROB_PURCHASE = _env_float("STREAM_PROB_PURCHASE", 0.12)

# ------------------------------
# Stream 디바이스/채널
# ------------------------------
STREAM_DEVICES = _env_list("STREAM_DEVICES", "web,android,ios")
STREAM_CHANNELS = _env_list("STREAM_CHANNELS", "organic,ads,email,push")

# ------------------------------
# Stream 프로모션 일자 자동 생성
# ------------------------------
PROMO_DAYS_MIN = _env_int("STREAM_PROMO_DAYS_MIN", 8)
PROMO_DAYS_MAX = _env_int("STREAM_PROMO_DAYS_MAX", 15)
STREAM_PROMOTION_BOOST = _env_float("STREAM_PROMO_BOOST", 3.0)

_stream_days = [STREAM_START_DATE + timedelta(days=i) for i in range(TOTAL_DAYS)]
STREAM_PROMOTION_DAYS = random.sample(
    _stream_days,
    k=random.randint(PROMO_DAYS_MIN, PROMO_DAYS_MAX)
)

# ------------------------------
# PA 설정 (정답 비교/무결성 목적)
# ------------------------------
PA_NUM_USERS = _env_int("PA_NUM_USERS", 3_000)  # 3천명 → 약 3만 row
PA_SIGNUP_WINDOW_DAYS = _env_int("PA_SIGNUP_WINDOW_DAYS", 30)

PA_SESSIONS_PER_USER = (
    _env_int("PA_SESSIONS_PER_USER_MIN", 1),
    _env_int("PA_SESSIONS_PER_USER_MAX", 6),
)
PA_EVENTS_PER_SESSION = (
    _env_int("PA_EVENTS_PER_SESSION_MIN", 1),
    _env_int("PA_EVENTS_PER_SESSION_MAX", 20),
)

PA_ORDER_RATE_IF_PURCHASE = _env_float("PA_ORDER_RATE_IF_PURCHASE", 0.65)

PA_COUNTRIES = _env_list("PA_COUNTRIES", "KR,US,JP")
PA_CHANNELS = _env_list("PA_CHANNELS", "organic,ad,referral")
PA_DEVICES = _env_list("PA_DEVICES", "ios,android,web")
PA_EVENT_NAMES = _env_list("PA_EVENT_NAMES", "view,click,add_to_cart,purchase")
