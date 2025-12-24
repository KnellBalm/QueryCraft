# problems/prompt.py
"""
문제 생성 래퍼 - generator.py에서 호출
prompt_pa와 gemini 모듈을 연결
"""
from __future__ import annotations

from engine.postgres_engine import PostgresEngine
from config.db import PostgresEnv
from problems.prompt_pa import build_pa_prompt
from problems.gemini import call_gemini_json
from common.logging import get_logger

logger = get_logger(__name__)


def get_data_summary() -> str:
    """현재 PA 데이터 요약 생성 - Gemini에게 정확한 스키마 정보 제공"""
    pg = PostgresEngine(PostgresEnv().dsn())
    
    try:
        summary_lines = ["## 테이블 구조 (PostgreSQL)"]
        
        # 테이블별 정보
        tables_info = [
            ("pa_users", "user_id (TEXT PK), signup_at (TIMESTAMP), country (TEXT), channel (TEXT)"),
            ("pa_sessions", "session_id (TEXT PK), user_id (TEXT FK), started_at (TIMESTAMP), device (TEXT)"),
            ("pa_events", "event_id (TEXT PK), user_id (TEXT FK), session_id (TEXT FK), event_time (TIMESTAMP), event_name (TEXT)"),
            ("pa_orders", "order_id (TEXT PK), user_id (TEXT FK), order_time (TIMESTAMP), amount (INT)")
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


def build_prompt() -> list[dict]:
    """
    generator.py에서 호출하는 메인 함수
    1. 현재 Product Type 조회
    2. 데이터 요약 생성
    3. Product Type 맞춤형 프롬프트 빌드
    4. Gemini 호출
    5. JSON 파싱 후 반환
    """
    # 현재 Product Type 조회
    product_type = get_current_product_type()
    logger.info(f"building PA problems prompt for product_type: {product_type}")
    
    data_summary = get_data_summary()
    logger.info(f"data summary generated:\n{data_summary}")
    
    # Product Type을 전달하여 맞춤형 프롬프트 생성
    prompt = build_pa_prompt(data_summary, n=6, product_type=product_type)
    logger.info("calling Gemini for problem generation")
    
    problems = call_gemini_json(prompt)
    logger.info(f"received {len(problems)} problems from Gemini")
    
    return problems

