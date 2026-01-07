# generator/product_profiles/content.py
"""
Content Product Profile
미디어/콘텐츠 플랫폼 - 소비 깊이(engagement) 중심
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import List

from .base import BaseProductProfile, Event


class ContentProfile(BaseProductProfile):
    """콘텐츠 플랫폼 프로필 - 읽기 깊이 + 소셜 인터랙션"""
    
    product_type = "content"
    
    def generate_session_events(
        self, 
        user_id: str, 
        session_id: str, 
        base_time: datetime
    ) -> List[Event]:
        """
        콘텐츠 세션 이벤트 생성
        - 핵심 플로우: page_view → read_content → scroll_25/50/75/100
        - 인터랙션: like, comment, share, bookmark
        - 구독 관련: subscribe, unsubscribe
        """
        events = []
        current_time = base_time
        probs = self.probabilities
        
        # 여러 콘텐츠 소비 (1-5개)
        num_contents = random.choices([1, 2, 3, 4, 5], weights=[0.25, 0.30, 0.25, 0.15, 0.05])[0]
        
        for content_idx in range(num_contents):
            # 1. 페이지뷰 (항상)
            events.append(self._create_event(user_id, session_id, current_time, "page_view"))
            current_time = self._add_time_offset(current_time, 2, 10)
            
            # 2. 콘텐츠 읽기 시작 (85%)
            if random.random() < probs["read_content"]:
                events.append(self._create_event(user_id, session_id, current_time, "read_content"))
                current_time = self._add_time_offset(current_time, 5, 30)
                
                # 스크롤 깊이 (점진적으로 확률 감소)
                scroll_events = ["scroll_25", "scroll_50", "scroll_75", "scroll_100"]
                for scroll_event in scroll_events:
                    if random.random() < probs[scroll_event]:
                        # 스크롤 이벤트 간 시간 (읽는 시간 시뮬레이션)
                        reading_time = random.randint(30, 120)  # 30초~2분
                        current_time = current_time + timedelta(seconds=reading_time)
                        events.append(self._create_event(user_id, session_id, current_time, scroll_event))
                    else:
                        break  # 스크롤 중단 = 이탈
                
                # 완독 후 인터랙션
                # 좋아요 (15%)
                if random.random() < probs["like"]:
                    events.append(self._create_event(user_id, session_id, current_time, "like"))
                    current_time = self._add_time_offset(current_time, 1, 3)
                
                # 북마크 (12%)
                if random.random() < probs["bookmark"]:
                    events.append(self._create_event(user_id, session_id, current_time, "bookmark"))
                    current_time = self._add_time_offset(current_time, 1, 3)
                
                # 댓글 (5%)
                if random.random() < probs["comment"]:
                    events.append(self._create_event(user_id, session_id, current_time, "comment"))
                    current_time = self._add_time_offset(current_time, 30, 180)  # 댓글 작성 시간
                
                # 공유 (8%)
                if random.random() < probs["share"]:
                    events.append(self._create_event(user_id, session_id, current_time, "share"))
                    current_time = self._add_time_offset(current_time, 5, 20)
            
            # 다음 콘텐츠로 이동 전 대기
            current_time = self._add_time_offset(current_time, 10, 60)
        
        # 구독 (세션 레벨)
        if random.random() < probs["subscribe"]:
            events.append(self._create_event(user_id, session_id, current_time, "subscribe"))
        elif random.random() < probs["unsubscribe"]:
            events.append(self._create_event(user_id, session_id, current_time, "unsubscribe"))
        
        # 시간순 정렬
        events.sort(key=lambda e: e.event_time)
        return events
