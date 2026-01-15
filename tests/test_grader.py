# tests/test_grader.py
"""
Grading 서비스 단위 테스트
"""
import pytest
import pandas as pd
from backend.services.grading_service import compare_results


class TestCompareResults:
    """compare_results 함수 테스트"""
    
    def test_identical_frames(self):
        """동일한 DataFrame은 정답"""
        df1 = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
        df2 = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
        is_correct, feedback = compare_results(df1, df2)
        assert is_correct is True
    
    def test_column_mismatch(self):
        """컬럼 불일치 시 오답"""
        df1 = pd.DataFrame({"a": [1], "b": [2]})
        df2 = pd.DataFrame({"a": [1], "c": [2]})
        is_correct, feedback = compare_results(df1, df2)
        assert is_correct is False
        assert "컬럼" in feedback
    
    def test_row_count_mismatch(self):
        """행 수 불일치 시 오답"""
        df1 = pd.DataFrame({"a": [1, 2, 3]})
        df2 = pd.DataFrame({"a": [1, 2]})
        is_correct, feedback = compare_results(df1, df2)
        assert is_correct is False
        assert "행" in feedback
    
    def test_value_mismatch(self):
        """값 불일치 시 오답"""
        df1 = pd.DataFrame({"a": [1, 2]})
        df2 = pd.DataFrame({"a": [1, 3]})
        is_correct, feedback = compare_results(df1, df2)
        assert is_correct is False
        assert "불일치" in feedback
    
    def test_with_sort_keys(self):
        """정렬 키 적용 후 비교"""
        df1 = pd.DataFrame({"id": [2, 1], "val": ["b", "a"]})
        df2 = pd.DataFrame({"id": [1, 2], "val": ["a", "b"]})
        is_correct, feedback = compare_results(df1, df2, sort_keys=["id"])
        assert is_correct is True
    
    def test_float_tolerance(self):
        """실수 비교 시 오차 허용"""
        df1 = pd.DataFrame({"a": [1.0000001]})
        df2 = pd.DataFrame({"a": [1.0000002]})
        is_correct, feedback = compare_results(df1, df2)
        assert is_correct is True
    
    def test_null_handling(self):
        """NaN 값 비교 (둘 다 NaN이면 일치)"""
        df1 = pd.DataFrame({"a": [1, None]})
        df2 = pd.DataFrame({"a": [1, None]})
        is_correct, feedback = compare_results(df1, df2)
        assert is_correct is True

    def test_null_mismatch(self):
        """한쪽만 NULL인 경우 오답"""
        df1 = pd.DataFrame({"a": [1, None]})
        df2 = pd.DataFrame({"a": [1, 2]})
        is_correct, feedback = compare_results(df1, df2)
        assert is_correct is False
        assert "불일치" in feedback

    def test_column_case_insensitive(self):
        """컬럼명 대소문자 무관"""
        df1 = pd.DataFrame({"USER_ID": [1, 2], "Name": ["a", "b"]})
        df2 = pd.DataFrame({"user_id": [1, 2], "name": ["a", "b"]})
        is_correct, feedback = compare_results(df1, df2)
        assert is_correct is True

    def test_string_whitespace_trimmed(self):
        """문자열 앞뒤 공백 무시"""
        df1 = pd.DataFrame({"a": ["hello ", " world"]})
        df2 = pd.DataFrame({"a": ["hello", "world"]})
        is_correct, feedback = compare_results(df1, df2)
        assert is_correct is True

    def test_empty_dataframes(self):
        """빈 DataFrame 비교"""
        df1 = pd.DataFrame({"a": []})
        df2 = pd.DataFrame({"a": []})
        is_correct, feedback = compare_results(df1, df2)
        assert is_correct is True

    def test_date_comparison(self):
        """날짜 비교 (DATE 부분만)"""
        from datetime import date, datetime
        df1 = pd.DataFrame({"dt": [date(2026, 1, 15)]})
        df2 = pd.DataFrame({"dt": [datetime(2026, 1, 15, 10, 30, 0)]})
        is_correct, feedback = compare_results(df1, df2)
        assert is_correct is True

    def test_date_string_comparison(self):
        """날짜 문자열 비교"""
        df1 = pd.DataFrame({"dt": ["2026-01-15"]})
        df2 = pd.DataFrame({"dt": ["2026-01-15 10:30:00"]})
        is_correct, feedback = compare_results(df1, df2)
        assert is_correct is True

    def test_large_dataframe(self):
        """대용량 DataFrame 비교 (벡터화 성능 테스트)"""
        import numpy as np
        n = 10000
        df1 = pd.DataFrame({
            "id": range(n),
            "value": np.random.rand(n),
            "text": [f"item_{i}" for i in range(n)]
        })
        df2 = df1.copy()
        is_correct, feedback = compare_results(df1, df2)
        assert is_correct is True

    def test_column_count_mismatch(self):
        """컬럼 수 불일치"""
        df1 = pd.DataFrame({"a": [1], "b": [2]})
        df2 = pd.DataFrame({"a": [1], "b": [2], "c": [3]})
        is_correct, feedback = compare_results(df1, df2)
        assert is_correct is False
        assert "컬럼 수" in feedback

    def test_multiple_sort_keys(self):
        """복수 정렬 키"""
        df1 = pd.DataFrame({
            "group": ["A", "B", "A", "B"],
            "id": [2, 1, 1, 2],
            "val": [4, 3, 2, 1]
        })
        df2 = pd.DataFrame({
            "group": ["A", "A", "B", "B"],
            "id": [1, 2, 1, 2],
            "val": [2, 4, 3, 1]
        })
        is_correct, feedback = compare_results(df1, df2, sort_keys=["group", "id"])
        assert is_correct is True

    def test_integer_float_comparison(self):
        """정수와 실수 비교"""
        df1 = pd.DataFrame({"a": [1, 2, 3]})
        df2 = pd.DataFrame({"a": [1.0, 2.0, 3.0]})
        is_correct, feedback = compare_results(df1, df2)
        assert is_correct is True
