# problems/generator_stream.py
"""Stream 문제 생성기 - 월별 JSON + 정답 통합"""
from __future__ import annotations

import json
import os
from datetime import date
from pathlib import Path
from typing import List

from backend.engine.postgres_engine import PostgresEngine
from problems.gemini import call_gemini_json
from backend.common.logging import get_logger

logger = get_logger(__name__)

PROBLEM_DIR = Path("problems/monthly")
PROBLEM_DIR.mkdir(parents=True, exist_ok=True)


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
                df = pg.fetch_df(f"SELECT COUNT(*) as cnt FROM public.{table_name}")
                count = int(df.iloc[0]["cnt"])
                summary_lines.append(f"- {table_name}: {count:,}건")
                summary_lines.append(f"  컬럼: {columns}")
            except Exception as e:
                summary_lines.append(f"- {table_name}: 조회 불가 ({e})")
        
        # 이벤트 유형
        try:
            df = pg.fetch_df("SELECT DISTINCT event_name FROM public.stream_events LIMIT 10")
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
                FROM public.stream_events
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
5. **submission_requirements**를 아래 5가지 항목 모두 포함하여 구체적으로 작성

[JSON 스키마]
{{
  "problem_id": "stream_sql_001",
  "difficulty": "easy | medium | hard",
  "topic": "funnel | revenue | dau | channel | device",
  "requester": "요청팀",
  "question": "업무 요청 형태로 작성. 필요 컬럼, 정렬 기준 명시",
  "context": "배경 설명",
  "submission_requirements": "제출 조건을 다음 형식으로 구체적으로 명시 (모든 항목 필수):
    1. 결과 컬럼: 'date, revenue, user_count' 순서로 출력
    2. 날짜 형식: 'YYYY-MM-DD' 형식 (예: DATE_TRUNC('day', event_time)::date)
    3. 숫자 형식: 소수점 2자리까지 반올림 (예: ROUND(rate::numeric, 2))
    4. 정렬: date 컬럼 기준 오름차순 정렬
    5. NULL 처리: NULL 값은 0으로 표시",
  "answer_sql": "PostgreSQL 정답 SQL",
  "expected_columns": ["col1", "col2"],
  "sort_keys": ["정렬 기준 컬럼"],
  "hint": "문제 해결 접근법 힌트 (예: '먼저 날짜별로 그룹화하고, 전환율을 계산한 후, 상위 N개를 추출하세요')"
}}

[CRITICAL - submission_requirements 작성 가이드]
**반드시 모든 문제에 다음 5가지 항목을 구체적으로 명시하라:**

1. **결과 컬럼**: 출력할 컬럼명과 순서를 정확히 나열
   - ❌ 나쁜 예: "날짜와 매출을 보여주세요"
   - ✅ 좋은 예: "date, revenue, user_count 순서로 출력"

2. **날짜 형식**: 날짜/시간 컬럼의 정확한 형식 지정
   - ❌ 나쁜 예: "날짜별로 집계"
   - ✅ 좋은 예: "날짜는 YYYY-MM-DD 형식으로 출력 (예: 2026-01-08)"

3. **숫자 형식**: 소수점 자릿수 명시
   - ❌ 나쁜 예: "전환율을 계산하세요"
   - ✅ 좋은 예: "비율은 소수점 2자리까지 반올림 (예: 0.15)"

4. **정렬**: 정렬 기준과 방향 명시
   - ❌ 나쁜 예: "정렬해주세요"
   - ✅ 좋은 예: "date 컬럼 기준 오름차순 정렬"

5. **NULL/결측값 처리**: NULL 값 처리 방법 명시
   - ❌ 나쁜 예: "값이 없으면 처리"
   - ✅ 좋은 예: "NULL 값은 0으로 표시, 데이터가 없는 날짜는 결과에서 제외"

[중요]
- answer_sql은 **위 테이블/컬럼만 사용**
- answer_sql의 결과가 submission_requirements와 100% 일치하도록 작성
- submission_requirements는 위 5가지 항목을 반드시 모두 포함
- JSON 배열 형식으로만 출력
""".strip()


def get_expected_result(pg: PostgresEngine, answer_sql: str, limit: int = 1000) -> list:
    """정답 SQL 실행하여 결과 데이터 반환"""
    try:
        # Remove SQL comments (single-line -- and multi-line /* */)
        import re
        # Remove multi-line comments /* ... */
        clean_sql = re.sub(r'/\*.*?\*/', '', answer_sql, flags=re.DOTALL)
        # Remove single-line comments --
        clean_sql = re.sub(r'--[^\n]*', '', clean_sql)
        # Remove extra whitespace and semicolons
        clean_sql = clean_sql.strip().rstrip(";")
        
        limited_sql = f"SELECT * FROM ({clean_sql}) AS _result LIMIT {limit}"
        df = pg.fetch_df(limited_sql)

        
        result = []
        for _, row in df.iterrows():
            record = {}
            for col in df.columns:
                val = row[col]
                if hasattr(val, 'isoformat'):
                    record[col] = val.isoformat()
                elif hasattr(val, 'item'):
                    record[col] = val.item()
                else:
                    record[col] = val
            result.append(record)
        
        return result
    except Exception as e:
        logger.error(f"Failed to get expected result: {e}")
        return []


def load_monthly_file(month_str: str) -> dict:
    """월별 JSON 파일 로드"""
    path = PROBLEM_DIR / f"stream_{month_str}.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"month": month_str, "problems": []}


def save_monthly_file(month_str: str, data: dict):
    """월별 JSON 파일 저장"""
    path = PROBLEM_DIR / f"stream_{month_str}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info(f"saved monthly stream file to {path}")


def save_problems_to_db(pg: PostgresEngine, problems: list, today: date, data_type: str):
    """문제를 PostgreSQL DB에 저장"""
    logger.info(f"saving {len(problems)} stream problems to DB for {today}")
    
    for p in problems:
        try:
            def clean_nan(obj):
                if isinstance(obj, float) and (obj != obj): # check for NaN
                    return None
                if isinstance(obj, dict):
                    return {k: clean_nan(v) for k, v in obj.items()}
                if isinstance(obj, list):
                    return [clean_nan(v) for v in obj]
                return obj

            p_clean = clean_nan(p)
            
            pg.execute("""
                INSERT INTO public.problems (
                    problem_date, data_type, set_index, difficulty, title, 
                    description, answer_sql, expected_columns, hints
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (problem_date, data_type, set_index, title) 
                DO UPDATE SET 
                    difficulty = EXCLUDED.difficulty,
                    description = EXCLUDED.description,
                    answer_sql = EXCLUDED.answer_sql,
                    expected_columns = EXCLUDED.expected_columns,
                    hints = EXCLUDED.hints,
                    updated_at = NOW()
            """, [
                today, 
                data_type, 
                p_clean.get("set_index", 0), 
                p_clean.get("difficulty"), 
                p_clean.get("problem_id"), 
                json.dumps(p_clean, ensure_ascii=False), # 전체 내용
                p_clean.get("answer_sql"),
                json.dumps(p_clean.get("expected_columns", []), ensure_ascii=False),
                json.dumps({"hint": p_clean.get("hint"), "expected_result": p_clean.get("expected_result")}, ensure_ascii=False)
            ])
        except Exception as e:
            logger.error(f"Failed to save stream problem {p.get('problem_id')} to DB: {e}")


def generate_stream_problems(target_date: date, pg: PostgresEngine) -> str:
    """Stream 문제 생성 - 월별 JSON에 누적 + DB 저장"""
    logger.info("generating stream problems for %s", target_date)
    
    month_str = target_date.strftime("%Y-%m")
    monthly_data = load_monthly_file(month_str)
    
    # 프롬프트 빌드 및 Gemini 호출
    data_summary = get_stream_data_summary(pg)
    prompt = build_stream_prompt(data_summary, n=6)
    problems = call_gemini_json(prompt)
    logger.info("generated %d stream problems from Gemini", len(problems))
    
    if not problems:
        return ""

    # 문제에 메타데이터 및 정답 결과 추가
    for p in problems:
        original_id = p["problem_id"]
        p["problem_id"] = f"{target_date}_{original_id}"
        p["date"] = target_date.isoformat()
        p["data_type"] = "stream"
        
        # XP 값 설정
        if "xp_value" not in p:
            diff = p.get("difficulty", "medium")
            if diff == "easy":
                p["xp_value"] = 3
            elif diff == "medium":
                p["xp_value"] = 5
            else:
                p["xp_value"] = 8
        
        # 정답 결과 데이터 생성
        answer_sql = p.get("answer_sql")
        if answer_sql:
            expected_result = get_expected_result(pg, answer_sql)
            p["expected_result"] = expected_result
            p["expected_row_count"] = len(expected_result)
        else:
            p["expected_result"] = []
            p["expected_row_count"] = 0
    
    # 1. DB 저장
    save_problems_to_db(pg, problems, target_date, "stream")

    # 2. 월별 파일에 추가
    monthly_data["problems"].extend(problems)
    save_monthly_file(month_str, monthly_data)
    
    # 3. 기존 daily 폴더 호환
    os.makedirs("problems/daily", exist_ok=True)
    daily_path = f"problems/daily/stream_{target_date.isoformat()}.json"
    with open(daily_path, "w", encoding="utf-8") as f:
        json.dump(problems, f, ensure_ascii=False, indent=2)
    
    logger.info("saved stream problems to DB and %s", daily_path)
    return str(PROBLEM_DIR / f"stream_{month_str}.json")
