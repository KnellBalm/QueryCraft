# generator/product_profiles/base.py
"""
BaseProductProfile - Strategy Pattern 인터페이스
모든 Product Profile은 이 클래스를 상속받아야 함
"""
from __future__ import annotations

import random
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from backend.generator.product_config import (
    get_events_for_type,
    get_probabilities_for_type,
    get_flow_for_type,
    get_kpi_guide,
)


@dataclass
class Event:
    """이벤트 데이터 클래스"""
    event_id: str
    user_id: str
    session_id: str
    event_time: datetime
    event_name: str
    properties: Optional[Dict] = None


class BaseProductProfile(ABC):
    """Product Profile 기본 클래스"""
    
    product_type: str = "base"
    
    @property
    def events(self) -> List[str]:
        """이 Product Type의 모든 이벤트"""
        return get_events_for_type(self.product_type)
    
    @property
    def probabilities(self) -> Dict[str, float]:
        """이벤트별 발생 확률"""
        return get_probabilities_for_type(self.product_type)
    
    @property
    def main_flow(self) -> List[str]:
        """주요 이벤트 플로우"""
        return get_flow_for_type(self.product_type)
    
    @property
    def kpi_guide(self) -> dict:
        """KPI 가이드"""
        return get_kpi_guide(self.product_type)
    
    @abstractmethod
    def generate_session_events(
        self, 
        user_id: str, 
        session_id: str, 
        base_time: datetime
    ) -> List[Event]:
        """
        세션 내 이벤트 시퀀스 생성
        
        Args:
            user_id: 사용자 ID
            session_id: 세션 ID
            base_time: 세션 시작 시간
            
        Returns:
            List[Event]: 생성된 이벤트 리스트
        """
        pass
    
    def get_activation_event(self) -> str:
        """Activation 이벤트 반환"""
        return self.kpi_guide.get("activation_event", self.events[0])
    
    def get_retention_events(self) -> List[str]:
        """Retention 측정 이벤트 반환"""
        return self.kpi_guide.get("retention_events", [self.events[0]])
    
    def _create_event(
        self, 
        user_id: str, 
        session_id: str, 
        event_time: datetime, 
        event_name: str,
        properties: Optional[Dict] = None
    ) -> Event:
        """Event 객체 생성 헬퍼"""
        return Event(
            event_id=str(uuid.uuid4()),
            user_id=user_id,
            session_id=session_id,
            event_time=event_time,
            event_name=event_name,
            properties=properties
        )
    
    def _should_trigger(self, event_name: str) -> bool:
        """확률에 따라 이벤트 발생 여부 결정"""
        prob = self.probabilities.get(event_name, 0.0)
        return random.random() < prob
    
    def _add_time_offset(self, base_time: datetime, min_seconds: int = 1, max_seconds: int = 120) -> datetime:
        """시간 오프셋 추가"""
        offset = random.randint(min_seconds, max_seconds)
        return base_time + timedelta(seconds=offset)


class FlowBasedProfile(BaseProductProfile):
    """플로우 기반 이벤트 생성 (funnel, engagement 등)"""
    
    def generate_session_events(
        self, 
        user_id: str, 
        session_id: str, 
        base_time: datetime
    ) -> List[Event]:
        """
        메인 플로우를 따라가며 확률적으로 이벤트 생성
        플로우 중간에 이탈할 수 있음
        """
        events = []
        current_time = base_time
        
        # 메인 플로우 따라가기
        for event_name in self.main_flow:
            if not self._should_trigger(event_name):
                break  # 이탈
            
            events.append(self._create_event(
                user_id, session_id, current_time, event_name
            ))
            current_time = self._add_time_offset(current_time)
        
        # 플로우 외 추가 이벤트 (랜덤)
        non_flow_events = [e for e in self.events if e not in self.main_flow]
        for event_name in non_flow_events:
            if self._should_trigger(event_name):
                events.append(self._create_event(
                    user_id, session_id, current_time, event_name
                ))
                current_time = self._add_time_offset(current_time, 1, 60)
        
        # 시간순 정렬
        events.sort(key=lambda e: e.event_time)
        return events
