# backend/services/skill_service.py
from __future__ import annotations
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd

from backend.services.database import postgres_connection
from backend.common.logging import get_logger

logger = get_logger(__name__)

SKILL_CATEGORIES = ['BASIC', 'AGGREGATE', 'JOIN', 'WINDOW', 'FUNNEL', 'RETENTION']

def update_user_skills(user_id: str, problem_id: str, is_correct: bool):
    """사용자의 문제 제출 결과에 따라 스킬 점수 업데이트"""
    if not user_id:
        return

    try:
        with postgres_connection() as pg:
            # 1. 문제의 카테고리 확인
            res = pg.fetch_df("SELECT category FROM public.problems WHERE id = %s OR description::jsonb->>'problem_id' = %s", (problem_id, problem_id))
            if len(res) == 0:
                logger.warning(f"Category not found for problem {problem_id}")
                return
            
            category = res.iloc[0]['category']
            if not category or category == 'N/A':
                category = 'BASIC' # Fallback
            
            # 2. user_skills 테이블 업데이트 (Upsert)
            # score 계산 로직: 
            # - 정답일 경우: +0.05 (최대 1.0)
            # - 오답일 경우: 0
            # - level: score * 10 (1~10레벨)
            
            score_increment = 0.05 if is_correct else 0.0
            correct_inc = 1 if is_correct else 0
            
            pg.execute("""
                INSERT INTO public.user_skills (user_id, category, score, level, correct_count, total_count, last_updated_at)
                VALUES (%s, %s, %s, %s, %s, 1, NOW())
                ON CONFLICT (user_id, category) DO UPDATE 
                SET 
                    score = LEAST(public.user_skills.score + %s, 1.0),
                    correct_count = public.user_skills.correct_count + %s,
                    total_count = public.user_skills.total_count + 1,
                    level = LEAST(FLOOR((public.user_skills.score + %s) * 10) + 1, 10),
                    last_updated_at = NOW()
            """, (user_id, category, score_increment, 1, correct_inc, score_increment, correct_inc, score_increment))
            
            logger.info(f"Updated skills for user {user_id}: category={category}, correct={is_correct}")
            
    except Exception as e:
        logger.error(f"Failed to update user skills: {e}")

def get_user_skill_profile(user_id: str) -> List[Dict]:
    """사용자의 전체 스킬 프로필 조회 (레이더 차트용)"""
    try:
        with postgres_connection() as pg:
            df = pg.fetch_df("SELECT category, score, level, correct_count, total_count FROM public.user_skills WHERE user_id = %s", (user_id,))
            
            # 모든 카테고리에 대해 결과 보장 (데이터가 없으면 0으로)
            existing_skills = {row['category']: row for _, row in df.iterrows()}
            profile = []
            
            for cat in SKILL_CATEGORIES:
                if cat in existing_skills:
                    profile.append(existing_skills[cat].to_dict())
                else:
                    profile.append({
                        "category": cat,
                        "score": 0.0,
                        "level": 1,
                        "correct_count": 0,
                        "total_count": 0
                    })
            
            return profile
    except Exception as e:
        logger.error(f"Failed to get user skill profile: {e}")
        return []

def get_weak_categories(user_id: str, limit: int = 2) -> List[str]:
    """사용자의 취약 카테고리(점수 최저) 추출"""
    try:
        profile = get_user_skill_profile(user_id)
        # 점수 순으로 정렬 (성취도가 낮은 순)
        sorted_profile = sorted(profile, key=lambda x: x['score'])
        return [p['category'] for p in sorted_profile[:limit]]
    except Exception:
        return ['BASIC', 'AGGREGATE']
