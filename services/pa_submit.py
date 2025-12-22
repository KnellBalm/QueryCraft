# services/pa_submit.py
from __future__ import annotations

from datetime import datetime
from typing import Dict, Any

import pandas as pd

from engine.postgres_engine import PostgresEngine
from engine.duckdb_engine import DuckDBEngine
from problems.gemini import grade_pa_submission
from common.logging import get_logger

logger = get_logger(__name__)

# ============================
# 환경: DB 엔진 선택
# ============================
# PA 정답 비교는 Postgres 기준 권장
pg = PostgresEngine()
duck = DuckDBEngine("data/pa_lab.duckdb")


# ============================
# 내부 헬퍼
# ============================
def _run_user_sql(sql_text: str) -> pd.DataFrame:
    """
    사용자 SQL 실행
    """
    logger.info("running user sql")
    return pg.query_df(sql_text)


def _run_answer_sql(problem_id: str) -> pd.DataFrame:
    """
    문제별 정답 SQL 실행
    ⚠️ 정답 SQL은 저장하지 않는다고 했으므로
    -> '정답 결과'를 생성하는 내부 쿼리를 문제 정의에서 가져온다고 가정
    """
    sql = duck.fetchone(
        """
        SELECT answer_sql
        FROM pa_answers
        WHERE problem_id = ?
        """,
        [problem_id],
    )["answer_sql"]

    logger.info(f"running answer sql for {problem_id}")
    return pg.query_df(sql)


def _compare_df(user_df: pd.DataFrame, answer_df: pd.DataFrame) -> Dict[str, Any]:
    """
    결과 비교 (엄격)
    """
    if list(user_df.columns) != list(answer_df.columns):
        return {
            "is_correct": False,
            "reason": "컬럼 구성이 다릅니다",
        }

    if len(user_df) != len(answer_df):
        return {
            "is_correct": False,
            "reason": "row 수가 다릅니다",
        }

    diff = (user_df != answer_df).any(axis=1)
    if diff.any():
        idx = diff.idxmax()
        col = (user_df.iloc[idx] != answer_df.iloc[idx]).idxmax()
        return {
            "is_correct": False,
            "reason": f"{idx+1}번째 row, {col} 컬럼 값이 다릅니다",
        }

    return {"is_correct": True}


# ============================
# 외부 진입점 (Streamlit / CLI 공용)
# ============================
def submit_pa(
    *,
    problem_id: str,
    sql_text: str,
    note: str | None = None,
    session_date: str,
) -> Dict[str, Any]:
    """
    PA 문제 제출 엔진
    """

    submitted_at = datetime.utcnow()
    logger.info(f"PA submit start problem_id={problem_id}")

    # ----------------------------
    # 1. 사용자 SQL 실행
    # ----------------------------
    try:
        user_df = _run_user_sql(sql_text)
    except Exception as e:
        logger.exception("user sql execution failed")
        feedback = grade_pa_submission(
            problem_id=problem_id,
            sql_text=sql_text,
            error=str(e),
            is_correct=False,
            diff=None,
            note=note,
        )
        _save_submission(
            problem_id,
            sql_text,
            False,
            feedback,
            session_date,
            submitted_at,
        )
        return {
            "is_correct": False,
            "feedback": feedback,
        }

    # ----------------------------
    # 2. 정답 SQL 실행
    # ----------------------------
    answer_df = _run_answer_sql(problem_id)

    # ----------------------------
    # 3. 결과 비교
    # ----------------------------
    cmp = _compare_df(user_df, answer_df)
    is_correct = cmp.get("is_correct", False)
    diff_reason = cmp.get("reason")

    # ----------------------------
    # 4. Gemini 채점
    # ----------------------------
    feedback = grade_pa_submission(
        problem_id=problem_id,
        sql_text=sql_text,
        is_correct=is_correct,
        diff=diff_reason,
        note=note,
    )

    # ----------------------------
    # 5. 저장
    # ----------------------------
    _save_submission(
        problem_id,
        sql_text,
        is_correct,
        feedback,
        session_date,
        submitted_at,
    )

    logger.info(f"PA submit done problem_id={problem_id} correct={is_correct}")

    return {
        "is_correct": is_correct,
        "feedback": feedback,
    }


# ============================
# DB 저장
# ============================
def _save_submission(
    problem_id: str,
    sql_text: str,
    is_correct: bool,
    feedback: str,
    session_date: str,
    submitted_at: datetime,
):
    duck.execute(
        """
        INSERT INTO pa_submissions
        (session_date, problem_id, sql_text, is_correct, feedback, submitted_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            session_date,
            problem_id,
            sql_text,
            is_correct,
            feedback,
            submitted_at,
        ],
    )
