# generator/product_profiles/community.py
"""
Community Product Profile
소셜/커뮤니티 플랫폼 - Creator/Consumer 중심
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import List

from .base import BaseProductProfile, Event


class CommunityProfile(BaseProductProfile):
    """커뮤니티 프로필 - 피드/포스팅/인터랙션"""
    
    product_type = "community"
    
    def generate_session_events(
        self, 
        user_id: str, 
        session_id: str, 
        base_time: datetime
    ) -> List[Event]:
        """
        커뮤니티 세션 이벤트 생성
        - 소비자 플로우: view_feed → profile_view → like → comment/reply
        - 창작자 플로우: view_feed → post_create/edit → comment
        - 소셜: follow/unfollow, message_send
        """
        events = []
        current_time = base_time
        probs = self.probabilities
        
        # 사용자 타입 결정 (20% 창작자, 80% 소비자)
        is_creator = random.random() < 0.20
        
        # 1. 피드 보기 (항상)
        events.append(self._create_event(user_id, session_id, current_time, "view_feed"))
        current_time = self._add_time_offset(current_time, 5, 30)
        
        # 피드 스크롤 - 여러 콘텐츠 소비
        num_feed_items = random.choices([3, 5, 10, 20, 30], weights=[0.2, 0.3, 0.25, 0.15, 0.1])[0]
        
        for _ in range(num_feed_items):
            # 좋아요 (35%)
            if random.random() < probs["like"]:
                events.append(self._create_event(user_id, session_id, current_time, "like"))
                current_time = self._add_time_offset(current_time, 1, 3)
            
            # 프로필 조회 (25%)
            if random.random() < probs["profile_view"]:
                events.append(self._create_event(user_id, session_id, current_time, "profile_view"))
                current_time = self._add_time_offset(current_time, 10, 60)
                
                # 팔로우 (12%)
                if random.random() < probs["follow"]:
                    events.append(self._create_event(user_id, session_id, current_time, "follow"))
                    current_time = self._add_time_offset(current_time, 1, 5)
                # 언팔로우 (3%)
                elif random.random() < probs["unfollow"]:
                    events.append(self._create_event(user_id, session_id, current_time, "unfollow"))
                    current_time = self._add_time_offset(current_time, 1, 5)
            
            # 댓글 (15%)
            if random.random() < probs["comment"]:
                events.append(self._create_event(user_id, session_id, current_time, "comment"))
                current_time = self._add_time_offset(current_time, 20, 120)  # 댓글 작성 시간
                
                # 대댓글 (10%)
                if random.random() < probs["reply"]:
                    events.append(self._create_event(user_id, session_id, current_time, "reply"))
                    current_time = self._add_time_offset(current_time, 15, 60)
            
            # 피드 스크롤 시간
            current_time = self._add_time_offset(current_time, 3, 15)
        
        # 창작자 행동
        if is_creator:
            # 포스트 작성 (8%)
            if random.random() < probs["post_create"]:
                events.append(self._create_event(user_id, session_id, current_time, "post_create"))
                current_time = self._add_time_offset(current_time, 120, 600)  # 포스트 작성 시간
                
                # 수정 (2%)
                if random.random() < probs["post_edit"]:
                    events.append(self._create_event(user_id, session_id, current_time, "post_edit"))
                    current_time = self._add_time_offset(current_time, 30, 180)
        
        # DM (8%)
        if random.random() < probs["message_send"]:
            num_messages = random.choices([1, 2, 3], weights=[0.6, 0.3, 0.1])[0]
            for _ in range(num_messages):
                events.append(self._create_event(user_id, session_id, current_time, "message_send"))
                current_time = self._add_time_offset(current_time, 30, 180)
        
        # 신고 (1%)
        if random.random() < probs["report"]:
            events.append(self._create_event(user_id, session_id, current_time, "report"))
        
        # 시간순 정렬
        events.sort(key=lambda e: e.event_time)
        return events
