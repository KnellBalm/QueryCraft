# shared/gemini_models.py
"""용도별 Gemini 모델 관리"""
import os
from google import genai

class GeminiModels:
    """용도별 Gemini 모델 - 무료 티어 할당량 분산"""
    
    # 모델 정의 (환경변수로 오버라이드 가능)
    PROBLEM_GENERATION = os.getenv("GEMINI_MODEL_PROBLEM", "gemini-2.5-flash")
    GRADING = os.getenv("GEMINI_MODEL_GRADING", "gemini-2.5-flash")
    TIPS = os.getenv("GEMINI_MODEL_TIPS", "gemini-2.5-flash-lite")
    HINTS = os.getenv("GEMINI_MODEL_HINTS", "gemini-2.5-flash-lite")
    ERROR_EXPLAIN = os.getenv("GEMINI_MODEL_ERROR", "gemini-3-flash")
    
    # 폴백 모델 (할당량 초과 시)
    FALLBACK = "gemini-1.5-flash"
    
    _client = None
    
    @classmethod
    def get_client(cls):
        """싱글톤 클라이언트"""
        if cls._client is None:
            cls._client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        return cls._client
    
    @classmethod
    def for_problem(cls):
        """문제 생성용 모델"""
        return cls.get_client(), cls.PROBLEM_GENERATION
    
    @classmethod
    def for_grading(cls):
        """채점용 모델"""
        return cls.get_client(), cls.GRADING
    
    @classmethod
    def for_tips(cls):
        """오늘의 팁용 모델 (경량)"""
        return cls.get_client(), cls.TIPS
    
    @classmethod
    def for_hints(cls):
        """힌트 생성용 모델 (경량)"""
        return cls.get_client(), cls.HINTS
    
    @classmethod
    def for_error(cls):
        """에러 설명용 모델"""
        return cls.get_client(), cls.ERROR_EXPLAIN
    
    @classmethod
    def for_purpose(cls, purpose: str):
        """용도별 모델 반환"""
        mapping = {
            "problem": cls.for_problem,
            "grading": cls.for_grading,
            "tips": cls.for_tips,
            "hints": cls.for_hints,
            "error": cls.for_error,
        }
        return mapping.get(purpose, cls.for_tips)()
