# grader/checker.py
from __future__ import annotations
import pandas as pd

class EngineError(Exception):
    def __init__(self, error_type: str, message: str):
        self.error_type = error_type
        self.message = message
        super().__init__(f"{error_type}: {message}")

class LogicError(Exception):
    def __init__(self, error_type: str, message: str):
        self.error_type = error_type
        self.message = message
        super().__init__(f"{error_type}: {message}")

def compare_frames(user_df: pd.DataFrame, expected_df: pd.DataFrame, sort_keys=None, float_tol=1e-9) -> None:
    # 컬럼
    if list(user_df.columns) != list(expected_df.columns):
        raise LogicError(
            "SCHEMA_MISMATCH",
            f"컬럼 불일치 expected={list(expected_df.columns)} got={list(user_df.columns)}"
        )

    # 행 수
    if len(user_df) != len(expected_df):
        raise LogicError(
            "ROW_COUNT_MISMATCH",
            f"행 수 불일치 expected={len(expected_df)} got={len(user_df)}"
        )

    # 정렬
    if sort_keys:
        missing = [k for k in sort_keys if k not in user_df.columns]
        if missing:
            raise LogicError("SCHEMA_MISMATCH", f"정렬 키 컬럼이 없습니다: {missing}")
        user_df = user_df.sort_values(sort_keys).reset_index(drop=True)
        expected_df = expected_df.sort_values(sort_keys).reset_index(drop=True)

    # 값 비교
    for i in range(len(user_df)):
        for col in user_df.columns:
            u = user_df.iloc[i][col]
            e = expected_df.iloc[i][col]

            if pd.isna(u) and pd.isna(e):
                continue

            # float tolerance
            if isinstance(u, float) or isinstance(e, float):
                try:
                    if abs(float(u) - float(e)) > float_tol:
                        raise LogicError("VALUE_MISMATCH", f"{i+1}번째 row, {col} 값 불일치 expected={e} got={u}")
                except Exception:
                    if u != e:
                        raise LogicError("VALUE_MISMATCH", f"{i+1}번째 row, {col} 값 불일치 expected={e} got={u}")
            else:
                if u != e:
                    hint = ""
                    lc = col.lower()
                    if "date" in lc or "time" in lc:
                        hint = " (날짜/시간 필터 범위를 점검해 보세요)"
                    if "user" in lc and ("cnt" in lc or "count" in lc):
                        hint = " (중복 제거/집계 기준을 점검해 보세요)"
                    raise LogicError("VALUE_MISMATCH", f"{i+1}번째 row, {col} 값 불일치 expected={e} got={u}{hint}")
