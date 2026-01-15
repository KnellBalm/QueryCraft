# backend/generator/validator.py
"""
데이터 품질 검증 클래스

생성된 데이터의 논리적 일관성을 검증합니다.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Any, List, Optional
from backend.common.logging import get_logger

logger = get_logger(__name__)

# datetime 포맷 규칙: 초 단위까지만 (마이크로초 제외)
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


@dataclass
class ValidationResult:
    """검증 결과"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    
    def to_dict(self) -> dict:
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings
        }


class DataValidator:
    """
    데이터 품질 검증 클래스
    
    검증 규칙:
    1. 퍼널 규칙: 상위 이벤트 >= 하위 이벤트
    2. 시간 순서 규칙: 시작 < 종료
    3. 수치 범위 규칙: 현실적인 범위 내 값
    4. datetime 포맷 규칙: YYYY-MM-DD HH:MM:SS
    """
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate_funnel(self, data: dict, rules: List[tuple]) -> ValidationResult:
        """
        퍼널 순서 검증
        
        Args:
            data: 검증할 데이터 딕셔너리
            rules: [(상위키, 하위키), ...] 형태의 규칙 리스트
            
        Example:
            validator.validate_funnel(
                {"page_views": 100, "downloads": 50},
                [("page_views", "downloads")]
            )
        """
        self.errors = []
        self.warnings = []
        
        for upper_key, lower_key in rules:
            upper_val = data.get(upper_key, 0)
            lower_val = data.get(lower_key, 0)
            
            if upper_val < lower_val:
                self.errors.append(
                    f"퍼널 위반: {upper_key}({upper_val}) < {lower_key}({lower_val})"
                )
        
        return ValidationResult(
            is_valid=len(self.errors) == 0,
            errors=self.errors,
            warnings=self.warnings
        )
    
    def validate_time_sequence(self, data: dict, rules: List[tuple]) -> ValidationResult:
        """
        시간 순서 검증
        
        Args:
            data: 검증할 데이터 딕셔너리
            rules: [(시작키, 종료키), ...] 형태의 규칙 리스트
        """
        self.errors = []
        self.warnings = []
        
        for start_key, end_key in rules:
            start_val = data.get(start_key)
            end_val = data.get(end_key)
            
            if start_val is None or end_val is None:
                continue
            
            # datetime 객체로 변환 시도
            try:
                if isinstance(start_val, str):
                    start_dt = datetime.strptime(start_val, DATETIME_FORMAT)
                else:
                    start_dt = start_val
                    
                if isinstance(end_val, str):
                    end_dt = datetime.strptime(end_val, DATETIME_FORMAT)
                else:
                    end_dt = end_val
                    
                if start_dt >= end_dt:
                    self.errors.append(
                        f"시간 순서 위반: {start_key}({start_val}) >= {end_key}({end_val})"
                    )
            except (ValueError, TypeError) as e:
                self.warnings.append(f"시간 파싱 실패: {start_key}/{end_key} - {e}")
        
        return ValidationResult(
            is_valid=len(self.errors) == 0,
            errors=self.errors,
            warnings=self.warnings
        )
    
    def validate_ranges(self, data: dict, rules: dict) -> ValidationResult:
        """
        수치 범위 검증
        
        Args:
            data: 검증할 데이터 딕셔너리
            rules: {키: (최소값, 최대값), ...} 형태의 규칙 딕셔너리
            
        Example:
            validator.validate_ranges(
                {"session_duration": 3600, "accuracy_rate": 85.5},
                {
                    "session_duration": (0, 86400),  # 0 ~ 24시간
                    "accuracy_rate": (0, 100)
                }
            )
        """
        self.errors = []
        self.warnings = []
        
        for key, (min_val, max_val) in rules.items():
            value = data.get(key)
            
            if value is None:
                continue
            
            try:
                num_val = float(value)
                if num_val < min_val or num_val > max_val:
                    self.errors.append(
                        f"범위 위반: {key}={num_val} (허용: {min_val}~{max_val})"
                    )
            except (ValueError, TypeError):
                self.warnings.append(f"숫자 변환 실패: {key}={value}")
        
        return ValidationResult(
            is_valid=len(self.errors) == 0,
            errors=self.errors,
            warnings=self.warnings
        )
    
    def validate_datetime_format(self, data: dict, keys: List[str]) -> ValidationResult:
        """
        datetime 포맷 검증 (YYYY-MM-DD HH:MM:SS)
        
        Args:
            data: 검증할 데이터 딕셔너리
            keys: datetime 형식이어야 하는 키 목록
        """
        self.errors = []
        self.warnings = []
        
        for key in keys:
            value = data.get(key)
            
            if value is None:
                continue
            
            if isinstance(value, datetime):
                # datetime 객체는 포맷 변환만 확인
                continue
            
            if isinstance(value, str):
                # ISO 8601 형식 (T, Z, 마이크로초) 체크
                if 'T' in value or 'Z' in value or '.' in value:
                    self.warnings.append(
                        f"datetime 포맷 권장사항: {key}='{value}' → "
                        f"'{DATETIME_FORMAT}' 형식 권장"
                    )
                
                # 파싱 가능 여부 확인
                try:
                    datetime.strptime(value[:19], DATETIME_FORMAT)
                except ValueError:
                    self.errors.append(
                        f"datetime 파싱 실패: {key}='{value}'"
                    )
        
        return ValidationResult(
            is_valid=len(self.errors) == 0,
            errors=self.errors,
            warnings=self.warnings
        )
    
    def validate_all(
        self, 
        data: dict,
        funnel_rules: Optional[List[tuple]] = None,
        time_rules: Optional[List[tuple]] = None,
        range_rules: Optional[dict] = None,
        datetime_keys: Optional[List[str]] = None
    ) -> ValidationResult:
        """
        모든 규칙을 한번에 검증
        """
        all_errors = []
        all_warnings = []
        
        if funnel_rules:
            result = self.validate_funnel(data, funnel_rules)
            all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)
        
        if time_rules:
            result = self.validate_time_sequence(data, time_rules)
            all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)
        
        if range_rules:
            result = self.validate_ranges(data, range_rules)
            all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)
        
        if datetime_keys:
            result = self.validate_datetime_format(data, datetime_keys)
            all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)
        
        is_valid = len(all_errors) == 0
        
        if not is_valid:
            logger.warning(f"데이터 검증 실패: {all_errors}")
        if all_warnings:
            logger.info(f"데이터 검증 경고: {all_warnings}")
        
        return ValidationResult(
            is_valid=is_valid,
            errors=all_errors,
            warnings=all_warnings
        )
