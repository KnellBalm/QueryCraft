# problems/prompt.py
"""
문제 생성 래퍼 - generator.py에서 호출
prompt_pa와 gemini 모듈을 연결
"""
from __future__ import annotations

import hashlib
import os

from backend.engine.postgres_engine import PostgresEngine
from backend.config.db import PostgresEnv
from problems.prompt_pa import build_pa_prompt
from problems.gemini import call_gemini_json
from problems.prompt_templates import PROMPT_VERSION
from backend.common.logging import get_logger

logger = get_logger(__name__)

PROMPT_AB_TEST_ENABLED = os.getenv("PROMPT_AB_TEST_ENABLED", "false").lower() in {"1", "true", "yes"}
PROMPT_AB_TEST_SALT = os.getenv("PROMPT_AB_TEST_SALT", "querycraft")


def get_experiment_group(user_id: str | None) -> str:
    """고정 그룹 분기 (기본값 A, A/B 테스트 비활성 시 A)"""
    if not PROMPT_AB_TEST_ENABLED or not user_id:
        return "A"
    hash_input = f"{user_id}:{PROMPT_AB_TEST_SALT}".encode("utf-8")
    digest = hashlib.sha256(hash_input).hexdigest()
    return "A" if int(digest, 16) % 2 == 0 else "B"


def get_prompt_metadata(user_id: str | None) -> dict:
    return {
        "prompt_version": PROMPT_VERSION,
        "experiment_group": get_experiment_group(user_id),
    }


def attach_prompt_metadata(problems: list[dict], metadata: dict) -> list[dict]:
    for problem in problems:
        problem.setdefault("prompt_version", metadata.get("prompt_version", PROMPT_VERSION))
        problem.setdefault("experiment_group", metadata.get("experiment_group", "A"))
    return problems


def get_data_summary() -> str:
    """현재 PA 데이터 요약 생성 - Gemini에게 정확한 스키마 정보 제공"""
    pg = PostgresEngine(PostgresEnv().dsn())
    
    try:
        summary_lines = ["## 테이블 구조 (PostgreSQL)"]
        
        # 테이블별 정보
        tables_info = [
            ("pa_users", "user_id (TEXT PK), signup_at (DATE), country (TEXT), channel (TEXT)"),
            ("pa_sessions", "session_id (TEXT PK), user_id (TEXT FK), started_at (TIMESTAMP), device (TEXT)"),
            ("pa_events", "event_id (TEXT PK), user_id (TEXT FK), session_id (TEXT FK), event_time (TIMESTAMP), event_name (TEXT)"),
            ("pa_orders", "order_id (TEXT PK), user_id (TEXT FK), order_time (DATE), amount (INT)")
        ]
        
        for table_name, columns in tables_info:
            try:
                df = pg.fetch_df(f"SELECT COUNT(*) as cnt FROM {table_name}")
                count = int(df.iloc[0]["cnt"])
                summary_lines.append(f"- {table_name}: {count:,}건")
                summary_lines.append(f"  컬럼: {columns}")
            except Exception as e:
                summary_lines.append(f"- {table_name}: 조회 불가 ({e})")
        
        # 이벤트 유형
        try:
            df = pg.fetch_df("SELECT DISTINCT event_name FROM pa_events LIMIT 15")
            event_names = [row["event_name"] for _, row in df.iterrows()]
            summary_lines.append(f"\n## 이벤트 유형 (event_name)")
            summary_lines.append(", ".join(event_names))
        except Exception:
            pass
        
        # 실제 데이터 날짜 범위
        try:
            date_df = pg.fetch_df("""
                SELECT 
                    MIN(signup_at)::date as min_date,
                    MAX(signup_at)::date as max_date
                FROM pa_users
            """)
            min_date = date_df.iloc[0]["min_date"]
            max_date = date_df.iloc[0]["max_date"]
            summary_lines.append(f"\n## 데이터 날짜 범위 (중요!)")
            summary_lines.append(f"- 가입일: {min_date} ~ {max_date}")
            summary_lines.append(f"- answer_sql 작성 시 이 범위 내 날짜 사용 필수")
        except Exception:
            pass
        
        # 주의사항
        summary_lines.append("\n## 주의사항")
        summary_lines.append("- answer_sql은 반드시 위 테이블/컬럼만 사용")
        summary_lines.append("- 존재하지 않는 컬럼 사용 금지 (예: signup_channel, event_type 없음)")
        summary_lines.append("- division by zero 방지: NULLIF 또는 CASE 사용")
        summary_lines.append("- 날짜 조건은 위 데이터 범위 내에서 사용")
        
        return "\n".join(summary_lines)
    finally:
        pg.close()


def get_current_product_type() -> str:
    """현재 데이터의 Product Type 조회 (default: commerce)"""
    pg = PostgresEngine(PostgresEnv().dsn())
    try:
        df = pg.fetch_df("SELECT product_type FROM current_product_type WHERE id = 1")
        if len(df) > 0:
            return str(df.iloc[0]["product_type"])
        return "commerce"  # 기본값
    except Exception:
        return "commerce"
    finally:
        pg.close()


def get_latest_anomaly_metadata(product_type: str) -> dict | None:
    """최신 RCA 이상 패턴 메타데이터 조회"""
    pg = PostgresEngine(PostgresEnv().dsn())
    try:
        # 가장 최근에 주입된 해당 산업군의 이상 패턴 조회
        df = pg.fetch_df("""
            SELECT anomaly_type, anomaly_params, description, hints, root_cause
            FROM public.rca_anomaly_metadata
            WHERE product_type = %s
            ORDER BY created_at DESC
            LIMIT 1
        """, (product_type,))
        
        if len(df) > 0:
            row = df.iloc[0]
            import json
            return {
                "type": row["anomaly_type"],
                "params": row["anomaly_params"] if isinstance(row["anomaly_params"], dict) else json.loads(row["anomaly_params"]),
                "description": row["description"],
                "hints": row["hints"] if isinstance(row["hints"], list) else json.loads(row["hints"]),
                "root_cause": row["root_cause"]
            }
        return None
    except Exception as e:
        logger.warning(f"Failed to fetch anomaly metadata: {e}")
        return None
    finally:
        pg.close()


def build_prompt(mode: str = "pa", user_id: str | None = None) -> list[dict]:
    """
    generator.py에서 호출하는 메인 함수 (통합 generator 아키텍처)
    1. 현재 Product Type 조회
    2. 데이터 요약 생성 (mode에 따라 다른 테이블)
    3. Product Type 및 Mode(pa/stream/rca) 맞춤형 프롬프트 빌드
    4. Gemini 호출
    5. JSON 파싱 후 반환
    6. 프롬프트 메타데이터 주입
    """
    # 현재 Product Type 조회
    product_type = get_current_product_type()
    logger.info(f"building {mode.upper()} problems prompt for product_type: {product_type}")

    # Mode에 따라 데이터 요약 및 프롬프트 생성 함수 선택
    if mode == "stream":
        from problems.prompt_stream import get_stream_data_summary, build_stream_prompt
        data_summary = get_stream_data_summary()
        logger.info(f"stream data summary generated:\n{data_summary}")
        prompt = build_stream_prompt(data_summary, n=6, product_type=product_type)
    elif mode == "rca":
        from problems.prompt_rca import build_rca_prompt
        data_summary = get_data_summary()
        logger.info(f"pa data summary generated:\n{data_summary}")
        anomaly_metadata = get_latest_anomaly_metadata(product_type)
        if anomaly_metadata:
            logger.info(f"Injecting anomaly metadata into RCA prompt: {anomaly_metadata['type']}")
        prompt = build_rca_prompt(data_summary, n=6, product_type=product_type, anomaly_metadata=anomaly_metadata)
    else:  # pa (default)
        data_summary = get_data_summary()
        logger.info(f"pa data summary generated:\n{data_summary}")
        prompt = build_pa_prompt(data_summary, n=6, product_type=product_type)

    logger.info(f"calling Gemini for {mode.upper()} problem generation")

    problems = call_gemini_json(prompt)
    logger.info(f"received {len(problems)} problems from Gemini")

    metadata = get_prompt_metadata(user_id)
    return attach_prompt_metadata(problems, metadata)

