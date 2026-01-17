# backend/services/recommendation_service.py
from __future__ import annotations
import json
import pandas as pd
from datetime import date, timedelta
from typing import List, Optional

from backend.schemas.problem import Problem
from backend.services.database import postgres_connection
from backend.common.date_utils import get_today_kst
from backend.common.logging import get_logger

logger = get_logger(__name__)

def get_recommended_problems(user_id: str, limit: int = 3) -> List[Problem]:
    """사용자에게 맞춤형 문제 추천 (취약점 기반)"""
    try:
        from backend.services.skill_service import get_weak_categories
        weak_cats = get_weak_categories(user_id, limit=2)
        
        with postgres_connection() as pg:
            # 1. 취약 카테고리 중 풀지 않은 문제 우선 조회
            df = pg.fetch_df("""
                SELECT p.description, p.data_type, p.problem_date, p.category
                FROM public.problems p
                LEFT JOIN public.submissions s ON s.problem_id = (p.description::jsonb)->>'problem_id' AND s.user_id = %s AND s.is_correct = true
                WHERE s.id IS NULL
                AND p.category = ANY(%s)
                ORDER BY p.problem_date DESC, RANDOM()
                LIMIT %s
            """, [user_id, weak_cats, limit])
            
            # 2. 부족하면 일반 미완료 문제로 보충
            if len(df) < limit:
                needed = limit - len(df)
                exclude_ids = [] # 이미 선택된 ID 제외 로직 생략 (limit이 작으므로)
                df_extra = pg.fetch_df("""
                    SELECT p.description, p.data_type, p.problem_date, p.category
                    FROM public.problems p
                    LEFT JOIN public.submissions s ON s.problem_id = (p.description::jsonb)->>'problem_id' AND s.user_id = %s AND s.is_correct = true
                    WHERE s.id IS NULL
                    ORDER BY p.problem_date DESC, RANDOM()
                    LIMIT %s
                """, [user_id, needed])
                df = pd.concat([df, df_extra]).drop_duplicates().head(limit)
            
            # 3. 그래도 부족하면 전체 랜덤 (복습)
            if len(df) == 0:
                df = pg.fetch_df("""
                    SELECT description, data_type, problem_date, category
                    FROM public.problems
                    ORDER BY RANDOM()
                    LIMIT %s
                """, [limit])
            
            problems = []
            for _, row in df.iterrows():
                desc = row["description"]
                p_data = json.loads(desc) if isinstance(desc, str) else desc
                problem = Problem(**p_data)
                
                # 메타데이터 보충
                problem.data_type = row["data_type"]
                # category 정보는 Problem 스키마에 없으므로 context 등을 통해 전달하거나 
                # 나중에 API에서 별도 처리 가능하게 note 등에 활용
                if not problem.context:
                    problem.context = ""
                problem.context += f" [추천 카테고리: {row['category']}]"
                
                problems.append(problem)
            
            return problems
            
    except Exception as e:
        logger.error(f"Failed to get recommended problems: {e}")
        return []

def get_reason_for_recommendation(user_id: str, problem_id: str) -> str:
    """추천 사유 생성 (데이터 기반)"""
    try:
        with postgres_connection() as pg:
            res = pg.fetch_df("SELECT category FROM public.problems WHERE description::jsonb->>'problem_id' = %s", (problem_id,))
            if len(res) > 0:
                category = res.iloc[0]['category']
                category_map = {
                    'JOIN': 'JOIN 활용 능력을 높일 수 있는 문제입니다.',
                    'AGGREGATE': '데이터 집계 및 그룹화 연습에 최적화된 문제입니다.',
                    'WINDOW': '복잡한 분석을 위한 윈도우 함수 실력을 키워보세요.',
                    'FUNNEL': '퍼널 분석 감각을 유지하는 데 도움이 됩니다.',
                    'RETENTION': '비즈니스의 핵심인 리텐션 분석 패턴입니다.',
                    'BASIC': '기본기를 탄탄하게 다지기 좋은 문제입니다.'
                }
                return category_map.get(category, "분석가님의 현재 진도에 딱 맞는 난이도입니다.")
                
        return "오늘의 분석 감각을 깨우기에 좋은 문제입니다."
    except:
        return "분석가님의 성장을 위해 엄선된 문제입니다."
