# problems/generator_stream.py
"""Stream 문제 생성기"""
from __future__ import annotations

import json
import os
from datetime import date
from typing import List

from engine.postgres_engine import PostgresEngine
from problems.gemini import call_gemini_json
from common.logging import get_logger

logger = get_logger(__name__)

GRADING_SCHEMA = "grading"


def get_stream_data_summary(pg: PostgresEngine) -> str:
    """Stream 데이터 요약 생성"""
    try:
        summary_lines = ["## 테이블 구조 (PostgreSQL - Stream 분석용)"]
        
        tables_info = [
            ("stream_events", "user_id (INT), session_id (TEXT), event_name (TEXT), event_time (TIMESTAMP), device (TEXT), channel (TEXT)"),
            ("stream_daily_metrics", "date (DATE), revenue (FLOAT), purchases (INT)")
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
            df = pg.fetch_df("SELECT DISTINCT event_name FROM stream_events LIMIT 10")
            event_names = [row["event_name"] for _, row in df.iterrows()]
            summary_lines.append(f"\n## 이벤트 유형 (event_name)")
            summary_lines.append(", ".join(event_names))
        except Exception:
            pass
        
        # 날짜 범위
        try:
            date_df = pg.fetch_df("""
                SELECT 
                    MIN(event_time)::date as min_date,
                    MAX(event_time)::date as max_date
                FROM stream_events
            """)
            min_date = date_df.iloc[0]["min_date"]
            max_date = date_df.iloc[0]["max_date"]
            summary_lines.append(f"\n## 데이터 날짜 범위")
            summary_lines.append(f"- 이벤트: {min_date} ~ {max_date}")
        except Exception:
            pass
        
        summary_lines.append("\n## 주의사항")
        summary_lines.append("- answer_sql은 반드시 위 테이블/컬럼만 사용")
        summary_lines.append("- 날짜 조건은 위 데이터 범위 내에서 사용")
        
        return "\n".join(summary_lines)
    except Exception:
        return "## Stream 데이터 요약 실패"


def build_stream_prompt(data_summary: str, n: int = 6) -> str:
    """Stream 문제 생성 프롬프트"""
    return f"""
너는 스트리밍 광고/마케팅 데이터 분석 전문가다.
아래 Stream 데이터를 기반으로 **실무 SQL 분석 문제와 정답**을 출제하라.

[데이터 요약]
{data_summary}

[출제 요구사항]
1. 총 {n}개 문제
2. 난이도 분배: easy 2개, medium 2개, hard 2개
3. 주제: 퍼널 분석, 일별 매출 추이, 채널별 성과, 디바이스별 전환율, DAU/MAU 등
4. **반드시 다른 팀/직무가 요청하는 형태**로 작성
5. **submission_requirements**에 정확한 제출 조건 명시 (컬럼명, 정렬 순서)

[JSON 스키마]
{{
  "problem_id": "stream_sql_001",
  "difficulty": "easy | medium | hard",
  "topic": "funnel | revenue | dau | channel | device",
  "requester": "요청팀",
  "question": "업무 요청 형태로 작성. 필요 컬럼, 정렬 기준 명시",
  "context": "배경 설명",
  "submission_requirements": "제출 조건 구체적으로 명시",
  "answer_sql": "PostgreSQL 정답 SQL",
  "expected_columns": ["col1", "col2"],
  "sort_keys": ["정렬 기준 컬럼"],
  "hint": "힌트"
}}

[중요]
- answer_sql은 **위 테이블/컬럼만 사용**
- JSON 배열 형식으로만 출력
""".strip()


def generate_stream_problems(target_date: date, pg: PostgresEngine) -> str:
    """Stream 문제 생성"""
    logger.info("generating stream problems for %s", target_date)
    
    # 데이터 요약
    data_summary = get_stream_data_summary(pg)
    logger.info("stream data summary:\n%s", data_summary)
    
    # 프롬프트 빌드 및 Gemini 호출
    prompt = build_stream_prompt(data_summary, n=6)
    problems = call_gemini_json(prompt)
    logger.info("generated %d stream problems from Gemini", len(problems))
    
    # grading 스키마에 expected 테이블 생성
    pg.execute(f"CREATE SCHEMA IF NOT EXISTS {GRADING_SCHEMA}")
    
    for p in problems:
        table = f"{GRADING_SCHEMA}.expected_{p['problem_id']}"
        answer_sql = p.get("answer_sql")
        
        if not answer_sql:
            logger.warning("answer_sql missing for %s", p['problem_id'])
            continue
        
        try:
            pg.execute(f"DROP TABLE IF EXISTS {table}")
            pg.execute(f"CREATE TABLE {table} AS {answer_sql}")
            
            df = pg.fetch_df(f"SELECT COUNT(*) as cnt FROM {table}")
            row_count = int(df.iloc[0]["cnt"])
            logger.info("created %s with %d rows", table, row_count)
            
            p["expected_meta"] = {"grading_table": f"expected_{p['problem_id']}"}
        except Exception as e:
            logger.warning("failed to create expected table for %s: %s", p['problem_id'], e)
    
    # 파일 저장
    os.makedirs("problems/daily", exist_ok=True)
    path = f"problems/daily/stream_{target_date.isoformat()}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(problems, f, ensure_ascii=False, indent=2)
    
    logger.info("saved stream problems to %s", path)
    return path
