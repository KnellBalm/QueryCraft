# config.py
import os
from pathlib import Path

# DuckDB (상태/로그/대시보드)
DUCKDB_PATH = Path(os.getenv("DUCKDB_PATH", "data/pa_lab.duckdb"))

# Postgres (연습/정답)
POSTGRES_DSN = os.getenv(
    "POSTGRES_DSN",
    "host=localhost port=5432 user=pa_lab password=pa_lab dbname=pa_lab",
)

# 문제 생성 옵션
USE_GEMINI = os.getenv("USE_GEMINI", "0") == "1"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyB6e0ciAyHp9fPnxXDERjQBQrSj7aDjAuw")

# 제출 기본값
DEFAULT_VIEW_NAME = os.getenv("DEFAULT_VIEW_NAME", "my_answer")
