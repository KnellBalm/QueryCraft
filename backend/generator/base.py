# backend/generator/base.py
"""
Generator 기본 추상 클래스

모든 데이터/문제 생성기는 이 클래스를 상속받아 구현합니다.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional
from backend.common.logging import get_logger

logger = get_logger(__name__)


@dataclass
class GenerationResult:
    """생성 결과를 담는 데이터 클래스"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    duration_seconds: float = 0.0
    metadata: Optional[dict] = None
    
    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "duration_seconds": self.duration_seconds,
            "metadata": self.metadata
        }


class BaseGenerator(ABC):
    """
    데이터/문제 생성기 추상 클래스
    
    모든 Generator는 이 클래스를 상속받아 다음 메서드를 구현해야 합니다:
    - generate(): 실제 생성 로직
    - validate(): 생성된 데이터 검증
    
    Example:
        class PAGenerator(BaseGenerator):
            def generate(self, date: str) -> GenerationResult:
                # PA 문제 생성 로직
                ...
                
            def validate(self) -> bool:
                # 검증 로직
                ...
    """
    
    def __init__(self, name: str):
        """
        Args:
            name: Generator 이름 (로깅용)
        """
        self.name = name
        self.last_result: Optional[GenerationResult] = None
        self._start_time: Optional[datetime] = None
    
    @abstractmethod
    def generate(self, date: str) -> GenerationResult:
        """
        데이터/문제 생성
        
        Args:
            date: 생성 대상 날짜 (YYYY-MM-DD)
            
        Returns:
            GenerationResult: 생성 결과
        """
        pass
    
    @abstractmethod
    def validate(self) -> bool:
        """
        생성된 데이터 검증
        
        Returns:
            bool: 검증 성공 여부
        """
        pass
    
    def run(self, date: str) -> GenerationResult:
        """
        생성 실행 (래퍼 메서드)
        
        시간 측정, 로깅, 예외 처리를 포함합니다.
        """
        import time
        
        logger.info(f"[{self.name}] Starting generation for {date}")
        self._start_time = datetime.now()
        start = time.time()
        
        try:
            result = self.generate(date)
            result.duration_seconds = time.time() - start
            
            if result.success:
                logger.info(f"[{self.name}] Generation completed in {result.duration_seconds:.2f}s")
            else:
                logger.error(f"[{self.name}] Generation failed: {result.error}")
                
            self.last_result = result
            return result
            
        except Exception as e:
            duration = time.time() - start
            logger.exception(f"[{self.name}] Generation exception: {e}")
            
            result = GenerationResult(
                success=False,
                error=str(e),
                duration_seconds=duration
            )
            self.last_result = result
            return result
    
    def log_result(self, result: GenerationResult) -> None:
        """결과를 DB 로그에 기록"""
        from backend.common.logging import db_log, LogCategory, LogLevel
        
        level = LogLevel.INFO if result.success else LogLevel.ERROR
        message = f"{self.name} 생성 {'성공' if result.success else '실패'}"
        
        if result.error:
            message += f": {result.error}"
        
        db_log(LogCategory.GENERATOR, message, level, self.name)
