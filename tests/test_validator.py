# tests/test_validator.py
"""
DataValidator 클래스 단위 테스트

TODO-list 매핑: IMPLEMENTATION_PLAN.md Section 1.3
"""
import pytest
from datetime import datetime
from backend.generator.validator import DataValidator, ValidationResult


class TestDataValidator:
    """DataValidator 클래스 테스트"""

    def setup_method(self):
        """각 테스트 전 실행"""
        self.validator = DataValidator()

    # ============ validate_funnel 테스트 ============

    def test_validate_funnel_success(self):
        """퍼널 검증 성공 케이스"""
        data = {
            "page_views": 1000,
            "downloads": 500,
            "signups": 250
        }
        rules = [
            ("page_views", "downloads"),
            ("downloads", "signups")
        ]

        result = self.validator.validate_funnel(data, rules)

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_funnel_violation(self):
        """퍼널 검증 실패 케이스 - 하위 > 상위"""
        data = {
            "page_views": 100,
            "downloads": 200  # 위반!
        }
        rules = [("page_views", "downloads")]

        result = self.validator.validate_funnel(data, rules)

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "퍼널 위반" in result.errors[0]

    def test_validate_funnel_edge_case_equal(self):
        """퍼널 검증 경계 케이스 - 동일한 값 (허용)"""
        data = {
            "page_views": 100,
            "downloads": 100
        }
        rules = [("page_views", "downloads")]

        result = self.validator.validate_funnel(data, rules)

        assert result.is_valid is True

    def test_validate_funnel_missing_key(self):
        """퍼널 검증 - 누락된 키 (기본값 0)"""
        data = {"page_views": 100}
        rules = [("page_views", "downloads")]

        result = self.validator.validate_funnel(data, rules)

        assert result.is_valid is True  # downloads=0 (기본값)

    # ============ validate_time_sequence 테스트 ============

    def test_validate_time_sequence_success_string(self):
        """시간 순서 검증 성공 - 문자열 타임스탬프"""
        data = {
            "session_start": "2026-01-16 10:00:00",
            "session_end": "2026-01-16 11:30:00"
        }
        rules = [("session_start", "session_end")]

        result = self.validator.validate_time_sequence(data, rules)

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_time_sequence_success_datetime(self):
        """시간 순서 검증 성공 - datetime 객체"""
        data = {
            "session_start": datetime(2026, 1, 16, 10, 0, 0),
            "session_end": datetime(2026, 1, 16, 11, 30, 0)
        }
        rules = [("session_start", "session_end")]

        result = self.validator.validate_time_sequence(data, rules)

        assert result.is_valid is True

    def test_validate_time_sequence_violation(self):
        """시간 순서 검증 실패 - 종료 < 시작"""
        data = {
            "session_start": "2026-01-16 11:00:00",
            "session_end": "2026-01-16 10:00:00"  # 위반!
        }
        rules = [("session_start", "session_end")]

        result = self.validator.validate_time_sequence(data, rules)

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "시간 순서 위반" in result.errors[0]

    def test_validate_time_sequence_equal_time(self):
        """시간 순서 검증 실패 - 동일한 시간 (위반)"""
        data = {
            "session_start": "2026-01-16 10:00:00",
            "session_end": "2026-01-16 10:00:00"
        }
        rules = [("session_start", "session_end")]

        result = self.validator.validate_time_sequence(data, rules)

        assert result.is_valid is False  # start >= end는 위반

    def test_validate_time_sequence_invalid_format(self):
        """시간 순서 검증 - 잘못된 포맷 (경고)"""
        data = {
            "session_start": "invalid-datetime",
            "session_end": "2026-01-16 11:00:00"
        }
        rules = [("session_start", "session_end")]

        result = self.validator.validate_time_sequence(data, rules)

        assert len(result.warnings) > 0
        assert "파싱 실패" in result.warnings[0]

    def test_validate_time_sequence_missing_keys(self):
        """시간 순서 검증 - 누락된 키 (무시)"""
        data = {"session_start": "2026-01-16 10:00:00"}
        rules = [("session_start", "session_end")]

        result = self.validator.validate_time_sequence(data, rules)

        assert result.is_valid is True  # 누락된 키는 검증하지 않음

    # ============ validate_ranges 테스트 ============

    def test_validate_ranges_success(self):
        """수치 범위 검증 성공"""
        data = {
            "session_duration": 3600,
            "accuracy_rate": 85.5,
            "user_age": 28
        }
        rules = {
            "session_duration": (0, 86400),  # 0~24시간
            "accuracy_rate": (0, 100),
            "user_age": (18, 65)
        }

        result = self.validator.validate_ranges(data, rules)

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_ranges_violation_below_min(self):
        """수치 범위 검증 실패 - 최소값 미만"""
        data = {"accuracy_rate": -5}
        rules = {"accuracy_rate": (0, 100)}

        result = self.validator.validate_ranges(data, rules)

        assert result.is_valid is False
        assert "범위 위반" in result.errors[0]

    def test_validate_ranges_violation_above_max(self):
        """수치 범위 검증 실패 - 최대값 초과"""
        data = {"accuracy_rate": 150}
        rules = {"accuracy_rate": (0, 100)}

        result = self.validator.validate_ranges(data, rules)

        assert result.is_valid is False
        assert "범위 위반" in result.errors[0]

    def test_validate_ranges_edge_case_boundaries(self):
        """수치 범위 검증 경계 케이스 - 경계값 (허용)"""
        data = {
            "accuracy_rate_min": 0,
            "accuracy_rate_max": 100
        }
        rules = {
            "accuracy_rate_min": (0, 100),
            "accuracy_rate_max": (0, 100)
        }

        result = self.validator.validate_ranges(data, rules)

        assert result.is_valid is True

    def test_validate_ranges_invalid_type(self):
        """수치 범위 검증 - 숫자 아님 (경고)"""
        data = {"accuracy_rate": "not-a-number"}
        rules = {"accuracy_rate": (0, 100)}

        result = self.validator.validate_ranges(data, rules)

        assert len(result.warnings) > 0
        assert "숫자 변환 실패" in result.warnings[0]

    def test_validate_ranges_missing_key(self):
        """수치 범위 검증 - 누락된 키 (무시)"""
        data = {}
        rules = {"accuracy_rate": (0, 100)}

        result = self.validator.validate_ranges(data, rules)

        assert result.is_valid is True  # 누락된 키는 검증하지 않음

    # ============ validate_datetime_format 테스트 ============

    def test_validate_datetime_format_success(self):
        """datetime 포맷 검증 성공"""
        data = {
            "created_at": "2026-01-16 10:30:45",
            "updated_at": datetime(2026, 1, 16, 11, 0, 0)
        }
        keys = ["created_at", "updated_at"]

        result = self.validator.validate_datetime_format(data, keys)

        assert result.is_valid is True

    def test_validate_datetime_format_iso8601_warning(self):
        """datetime 포맷 경고 - ISO 8601 형식"""
        data = {
            "created_at": "2026-01-16T10:30:45.123456Z"
        }
        keys = ["created_at"]

        result = self.validator.validate_datetime_format(data, keys)

        assert result.is_valid is True
        assert len(result.warnings) > 0
        assert "포맷 권장사항" in result.warnings[0]

    def test_validate_datetime_format_invalid(self):
        """datetime 포맷 검증 실패 - 파싱 불가"""
        data = {
            "created_at": "invalid-datetime-format"
        }
        keys = ["created_at"]

        result = self.validator.validate_datetime_format(data, keys)

        assert result.is_valid is False
        assert "파싱 실패" in result.errors[0]

    # ============ validate_all 통합 테스트 ============

    def test_validate_all_success(self):
        """통합 검증 성공 - 모든 규칙 통과"""
        data = {
            "page_views": 1000,
            "downloads": 500,
            "session_start": "2026-01-16 10:00:00",
            "session_end": "2026-01-16 11:00:00",
            "session_duration": 3600,
            "accuracy_rate": 95.5,
            "created_at": "2026-01-16 09:00:00"
        }

        result = self.validator.validate_all(
            data,
            funnel_rules=[("page_views", "downloads")],
            time_rules=[("session_start", "session_end")],
            range_rules={
                "session_duration": (0, 86400),
                "accuracy_rate": (0, 100)
            },
            datetime_keys=["created_at"]
        )

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_all_multiple_violations(self):
        """통합 검증 실패 - 여러 규칙 위반"""
        data = {
            "page_views": 100,
            "downloads": 200,  # 퍼널 위반
            "session_start": "2026-01-16 11:00:00",
            "session_end": "2026-01-16 10:00:00",  # 시간 위반
            "accuracy_rate": 150  # 범위 위반
        }

        result = self.validator.validate_all(
            data,
            funnel_rules=[("page_views", "downloads")],
            time_rules=[("session_start", "session_end")],
            range_rules={"accuracy_rate": (0, 100)}
        )

        assert result.is_valid is False
        assert len(result.errors) == 3  # 3개 규칙 모두 위반

    def test_validate_all_warnings_only(self):
        """통합 검증 - 경고만 있는 케이스"""
        data = {
            "created_at": "2026-01-16T10:30:45.123456Z",  # 포맷 경고
            "accuracy_rate": "not-a-number"  # 숫자 변환 경고
        }

        result = self.validator.validate_all(
            data,
            datetime_keys=["created_at"],
            range_rules={"accuracy_rate": (0, 100)}
        )

        assert result.is_valid is True  # 경고만으로는 실패 아님
        assert len(result.warnings) == 2

    # ============ 실제 사용 시나리오 테스트 ============

    def test_real_world_scenario_ecommerce_funnel(self):
        """실제 시나리오 - 이커머스 퍼널"""
        data = {
            "product_views": 10000,
            "add_to_cart": 3000,
            "checkout": 1500,
            "purchase": 1200
        }
        funnel_rules = [
            ("product_views", "add_to_cart"),
            ("add_to_cart", "checkout"),
            ("checkout", "purchase")
        ]

        result = self.validator.validate_funnel(data, funnel_rules)

        assert result.is_valid is True

    def test_real_world_scenario_session_data(self):
        """실제 시나리오 - 세션 데이터"""
        data = {
            "session_start": "2026-01-16 10:00:00",
            "session_end": "2026-01-16 10:45:30",
            "session_duration": 2730,  # 45.5분 = 2730초
            "page_views": 15,
            "events_count": 42
        }

        result = self.validator.validate_all(
            data,
            time_rules=[("session_start", "session_end")],
            range_rules={
                "session_duration": (0, 86400),
                "page_views": (1, 1000),
                "events_count": (0, 10000)
            },
            datetime_keys=["session_start", "session_end"]
        )

        assert result.is_valid is True

    def test_real_world_scenario_problem_submission(self):
        """실제 시나리오 - 문제 제출 데이터"""
        data = {
            "problem_viewed": 1000,
            "problem_attempted": 800,
            "problem_submitted": 600,
            "problem_solved": 450,
            "started_at": "2026-01-16 10:00:00",
            "submitted_at": "2026-01-16 10:25:00",
            "time_spent_minutes": 25,
            "attempt_count": 3
        }

        result = self.validator.validate_all(
            data,
            funnel_rules=[
                ("problem_viewed", "problem_attempted"),
                ("problem_attempted", "problem_submitted"),
                ("problem_submitted", "problem_solved")
            ],
            time_rules=[("started_at", "submitted_at")],
            range_rules={
                "time_spent_minutes": (0, 180),  # 최대 3시간
                "attempt_count": (1, 100)
            },
            datetime_keys=["started_at", "submitted_at"]
        )

        assert result.is_valid is True


class TestValidationResult:
    """ValidationResult 데이터클래스 테스트"""

    def test_validation_result_to_dict(self):
        """ValidationResult to_dict 메서드"""
        result = ValidationResult(
            is_valid=False,
            errors=["에러 1", "에러 2"],
            warnings=["경고 1"]
        )

        result_dict = result.to_dict()

        assert result_dict == {
            "is_valid": False,
            "errors": ["에러 1", "에러 2"],
            "warnings": ["경고 1"]
        }

    def test_validation_result_empty(self):
        """ValidationResult 빈 결과"""
        result = ValidationResult(
            is_valid=True,
            errors=[],
            warnings=[]
        )

        assert result.is_valid is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 0
