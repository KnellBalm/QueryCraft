# backend/schemas/submission.py
"""제출 관련 스키마"""
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime


class SQLExecuteRequest(BaseModel):
    """SQL 실행 요청"""
    sql: str = Field(..., min_length=1)
    limit: int = Field(default=100, ge=1, le=1000)


class SQLExecuteResponse(BaseModel):
    """SQL 실행 응답"""
    success: bool
    columns: Optional[List[str]] = None
    data: Optional[List[dict]] = None
    row_count: Optional[int] = None
    execution_time_ms: Optional[float] = None
    error: Optional[str] = None


class SubmitRequest(BaseModel):
    """문제 제출 요청"""
    problem_id: str
    sql: str
    data_type: str = "pa"
    note: Optional[str] = None


class SubmitResponse(BaseModel):
    """문제 제출 응답"""
    is_correct: bool
    feedback: str
    execution_time_ms: Optional[float] = None
    diff: Optional[str] = None


class SubmissionHistory(BaseModel):
    """제출 이력"""
    problem_id: str
    session_date: str
    is_correct: bool
    submitted_at: datetime
    feedback: Optional[str] = None


class UserStats(BaseModel):
    """사용자 통계"""
    streak: int
    max_streak: int
    level: str
    total_solved: int
    correct: int
    accuracy: float
    next_level_threshold: int
    score: int = 0
    level_progress: int = 0


class InsightRequest(BaseModel):
    """AI 인사이트 요청"""
    problem_id: str
    sql: str
    results: List[dict]
    data_type: str = "pa"


class SuggestedQuery(BaseModel):
    """추천 쿼리"""
    title: str
    sql: str


class InsightResponse(BaseModel):
    """AI 인사이트 응답"""
    key_findings: List[str] = Field(default_factory=list, description="핵심 발견 사항")
    insights: List[str] = Field(default_factory=list, description="비즈니스 인사이트")
    action_items: List[str] = Field(default_factory=list, description="추천 액션")
    suggested_queries: List[SuggestedQuery] = Field(default_factory=list, description="추가 분석 제안")
    report_markdown: str = Field(default="", description="마크다운 형식 리포트")
    
    # 하위 호환성 위해 유지 (deprecated)
    insight: Optional[str] = None


class TranslateRequest(BaseModel):
    """Text-to-SQL 요청"""
    question: str
    data_type: str = "pa"


class TranslateResponse(BaseModel):
    """Text-to-SQL 응답"""
    sql: str

