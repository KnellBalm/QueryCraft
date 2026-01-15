# backend/generator/__init__.py
"""
데이터/문제 생성 모듈

이 모듈은 다양한 유형의 데이터와 문제를 생성하는 Generator 클래스들을 제공합니다.

사용 예시:
    from backend.generator.base import BaseGenerator, GenerationResult
    from backend.generator.validator import DataValidator
"""
from backend.generator.base import BaseGenerator, GenerationResult
from backend.generator.validator import DataValidator, ValidationResult

__all__ = [
    "BaseGenerator",
    "GenerationResult",
    "DataValidator",
    "ValidationResult",
]
