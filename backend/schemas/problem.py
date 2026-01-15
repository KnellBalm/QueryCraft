# backend/schemas/problem.py
"""문제 관련 스키마"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class TableColumn(BaseModel):
    """테이블 컬럼 정보"""
    column_name: str
    data_type: str


class TableSchema(BaseModel):
    """테이블 스키마"""
    table_name: str
    columns: List[TableColumn]
    row_count: Optional[int] = None


class Problem(BaseModel):
    """문제 정보"""
    problem_id: str
    difficulty: str = Field(..., pattern="^(easy|medium|hard)$")
    topic: str
    requester: Optional[str] = None
    question: str
    context: Optional[str] = None
    expected_description: Optional[str] = None
    expected_columns: Optional[List[str]] = None
    sort_keys: Optional[List[str]] = None
    hint: Optional[str] = None
    hints: Optional[List[str]] = None  # Progressive hints array (for RCA)
    anomaly_metadata_id: Optional[int] = None  # Link to rca_anomaly_metadata table

    # 채점 관련 필드
    answer_sql: Optional[str] = None
    expected_result: Optional[List[dict]] = None
    expected_meta: Optional[dict] = None
    xp_value: Optional[int] = 5
    
    # 상태 정보 (조회 시 추가)
    is_completed: Optional[bool] = None
    is_correct: Optional[bool] = None


class DatasetMetadata(BaseModel):
    """데이터셋 메타데이터 (배경 설명용)"""
    company_name: str
    company_description: str
    product_type: str
    north_star: Optional[str] = None
    key_metrics: Optional[List[str]] = None


class ProblemListResponse(BaseModel):
    """문제 목록 응답"""
    date: str
    data_type: str  # pa | stream
    problems: List[Problem]
    total: int
    completed: int
    metadata: Optional[DatasetMetadata] = None


class ProblemDetailResponse(BaseModel):
    """문제 상세 응답"""
    problem: Problem
    tables: List[TableSchema]
    metadata: Optional[DatasetMetadata] = None
