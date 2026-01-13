# backend/schemas/stats.py
"""통계 관련 스키마"""
from pydantic import BaseModel
from typing import Optional


class LevelInfo(BaseModel):
    """레벨 정보"""
    name: str
    score: int
    next: int
    correct: int
    progress: int


class UserStats(BaseModel):
    """사용자 통계"""
    streak: int = 0
    max_streak: int = 0
    level: str = "🌱 Beginner"
    total_solved: int = 0
    correct: int = 0
    accuracy: float = 0.0
    next_level_threshold: int = 50
    score: int = 0
    level_progress: int = 0
