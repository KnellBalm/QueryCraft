# backend/services/recommendation_service.py
from __future__ import annotations
import json
import random
from datetime import date, timedelta
from typing import List, Optional

from backend.schemas.problem import Problem
from backend.services.database import postgres_connection
from backend.common.date_utils import get_today_kst
from backend.common.logging import get_logger

logger = get_logger(__name__)

def get_recommended_problems(user_id: str, limit: int = 3) -> List[Problem]:
    """사용자에게 맞춤형 문제 추천"""
    today = get_today_kst()
    
    try:
        with postgres_connection() as pg:
            # 1. 사용자가 풀지 않은 문제 중 최근 것부터 조회
            # 서브쿼리로 이미 푼 문제 제외
            df = pg.fetch_df("""
                SELECT p.description, p.data_type, p.problem_date
                FROM public.problems p
                LEFT JOIN public.submissions s ON s.problem_id = (p.description::jsonb)->>'problem_id' AND s.user_id = %s AND s.is_correct = true
                WHERE s.id IS NULL
                ORDER BY p.problem_date DESC, RANDOM()
                LIMIT %s
            """, [user_id, limit])
            
            if len(df) == 0:
                # 다 풀었거나 문제가 없는 경우, 무작위로 추천 (복습 권장)
                df = pg.fetch_df("""
                    SELECT description, data_type, problem_date
                    FROM public.problems
                    ORDER BY RANDOM()
                    LIMIT %s
                """, [limit])
            
            problems = []
            for _, row in df.iterrows():
                desc = row["description"]
                p_data = json.loads(desc) if isinstance(desc, str) else desc
                problem = Problem(**p_data)
                
                # 메타데이터 수동 보충 (Problem schema 필드와 DB 컬럼 불일치 대응)
                if not problem.data_type:
                    problem.data_type = row["data_type"]
                
                problems.append(problem)
            
            return problems
            
    except Exception as e:
        logger.error(f"Failed to get recommended problems: {e}")
        return []

def get_reason_for_recommendation(user_id: str, problem_id: str) -> str:
    """추천 사유 생성 (간단하게 데이터 기반으로)"""
    # 실제로는 더 정교한 로직(X차 시도 중, 유사 유형 정답률 등)이 들어가야 함
    reasons = [
        "분석가님의 현재 진도에 딱 맞는 난이도입니다.",
        "이전에 자주 틀렸던 유형의 보완을 위해 추천합니다.",
        "실무에서 가장 많이 활용되는 분석 패턴입니다.",
        "오늘의 분석 감각을 깨우기에 좋은 문제입니다.",
        "동료 분석가들이 가장 많이 도전하고 있는 문제입니다."
    ]
    return random.choice(reasons)
