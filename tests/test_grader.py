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
