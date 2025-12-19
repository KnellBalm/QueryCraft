# grader/grader.py
import pandas as pd

class EngineError(Exception):
    def __init__(self, error_type, message):
        self.error_type = error_type
        self.message = message

class LogicError(Exception):
    def __init__(self, error_type, message):
        self.error_type = error_type
        self.message = message

def grade(pg, problem, view_name="my_answer"):
    pid = problem["problem_id"]

    try:
        user_df = pg.fetch_df(f"SELECT * FROM {view_name}")
    except Exception as e:
        raise EngineError("SQL_EXECUTION_ERROR", str(e))

    try:
        expected_df = pg.fetch_df(f"SELECT * FROM expected_{pid}")
    except Exception as e:
        raise EngineError("EXPECTED_TABLE_ERROR", str(e))

    if list(user_df.columns) != list(expected_df.columns):
        raise LogicError(
            "SCHEMA_MISMATCH",
            f"컬럼 불일치: expected={list(expected_df.columns)}, got={list(user_df.columns)}"
        )

    if len(user_df) != len(expected_df):
        raise LogicError(
            "ROW_COUNT_MISMATCH",
            f"행 수 불일치: expected={len(expected_df)}, got={len(user_df)}"
        )

    sort_keys = problem.get("sort_keys")
    if sort_keys:
        user_df = user_df.sort_values(sort_keys).reset_index(drop=True)
        expected_df = expected_df.sort_values(sort_keys).reset_index(drop=True)

    for i in range(len(user_df)):
        for col in user_df.columns:
            u, e = user_df.iloc[i][col], expected_df.iloc[i][col]
            if pd.isna(u) and pd.isna(e):
                continue
            if u != e:
                raise LogicError(
                    "VALUE_MISMATCH",
                    f"{i+1}번째 row {col} 값 불일치: expected={e}, got={u}"
                )

    return True
