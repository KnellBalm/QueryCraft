# generator/product_profiles/saas.py
"""
SaaS Product Profile
B2B SaaS 플랫폼 - Feature Adoption + Activation 중심
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import List

from .base import BaseProductProfile, Event


class SaaSProfile(BaseProductProfile):
    """SaaS 프로필 - 로그인/기능 사용/프로젝트 관리"""
    
    product_type = "saas"
    
    def generate_session_events(
        self, 
        user_id: str, 
        session_id: str, 
        base_time: datetime
    ) -> List[Event]:
        """
        SaaS 세션 이벤트 생성
        - 핵심 플로우: login → dashboard_view → feature_use → create_project
        - 협업: invite_member
        - 데이터: export_data, api_call
        - 구독: upgrade/downgrade/cancel
        """
        events = []
        current_time = base_time
        probs = self.probabilities
        
        # 1. 로그인 (항상)
        events.append(self._create_event(user_id, session_id, current_time, "login"))
        current_time = self._add_time_offset(current_time, 2, 8)
        
        # 2. 대시보드 조회 (95%)
        if random.random() < probs["dashboard_view"]:
            events.append(self._create_event(user_id, session_id, current_time, "dashboard_view"))
            current_time = self._add_time_offset(current_time, 10, 60)
        
        # 온보딩 완료 (신규 사용자, 40%)
        if random.random() < probs["onboarding_complete"]:
            events.append(self._create_event(user_id, session_id, current_time, "onboarding_complete"))
            current_time = self._add_time_offset(current_time, 60, 300)  # 온보딩 시간
        
        # 3. 기능 사용 (여러 번 가능)
        if random.random() < probs["feature_use"]:
            num_features = random.choices([1, 2, 3, 4, 5, 6], weights=[0.2, 0.25, 0.25, 0.15, 0.1, 0.05])[0]
            for _ in range(num_features):
                events.append(self._create_event(user_id, session_id, current_time, "feature_use"))
                current_time = self._add_time_offset(current_time, 60, 300)  # 기능 사용 시간
        
        # 4. 프로젝트 생성 (20%)
        if random.random() < probs["create_project"]:
            events.append(self._create_event(user_id, session_id, current_time, "create_project"))
            current_time = self._add_time_offset(current_time, 30, 120)
        
        # 5. 멤버 초대 (8%)
        if random.random() < probs["invite_member"]:
            num_invites = random.choices([1, 2, 3], weights=[0.6, 0.3, 0.1])[0]
            for _ in range(num_invites):
                events.append(self._create_event(user_id, session_id, current_time, "invite_member"))
                current_time = self._add_time_offset(current_time, 10, 30)
        
        # 6. 데이터 내보내기 (15%)
        if random.random() < probs["export_data"]:
            events.append(self._create_event(user_id, session_id, current_time, "export_data"))
            current_time = self._add_time_offset(current_time, 5, 30)
        
        # 7. API 호출 (25%)
        if random.random() < probs["api_call"]:
            num_calls = random.choices([1, 5, 10, 20], weights=[0.4, 0.3, 0.2, 0.1])[0]
            for _ in range(num_calls):
                events.append(self._create_event(user_id, session_id, current_time, "api_call"))
                current_time = self._add_time_offset(current_time, 1, 10)
        
        # 8. 고객지원 티켓 (5%)
        if random.random() < probs["support_ticket"]:
            events.append(self._create_event(user_id, session_id, current_time, "support_ticket"))
            current_time = self._add_time_offset(current_time, 60, 300)  # 티켓 작성 시간
        
        # 9. 플랜 변경 (낮은 확률)
        if random.random() < probs["upgrade_plan"]:
            events.append(self._create_event(user_id, session_id, current_time, "upgrade_plan"))
        elif random.random() < probs["downgrade_plan"]:
            events.append(self._create_event(user_id, session_id, current_time, "downgrade_plan"))
        elif random.random() < probs["cancel_subscription"]:
            events.append(self._create_event(user_id, session_id, current_time, "cancel_subscription"))
        
        # 10. 로그아웃 (90%)
        if random.random() < probs["logout"]:
            events.append(self._create_event(user_id, session_id, current_time, "logout"))
        
        # 시간순 정렬
        events.sort(key=lambda e: e.event_time)
        return events
