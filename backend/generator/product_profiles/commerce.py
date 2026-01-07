# generator/product_profiles/commerce.py
"""
Commerce Product Profile
이커머스 플랫폼 - 구매 퍼널 중심
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import List

from .base import BaseProductProfile, Event


class CommerceProfile(BaseProductProfile):
    """이커머스 프로필 - 구매 퍼널 + 다양한 쇼핑 행동"""
    
    product_type = "commerce"
    
    def generate_session_events(
        self, 
        user_id: str, 
        session_id: str, 
        base_time: datetime
    ) -> List[Event]:
        """
        커머스 세션 이벤트 생성
        - 핵심 퍼널: page_view → search → view_product → add_to_cart → checkout → purchase
        - 각 단계에서 확률적으로 이탈
        - 추가 행동: 리뷰 보기, 위시리스트, 쿠폰, 비교 등
        """
        events = []
        current_time = base_time
        probs = self.probabilities
        
        # 1. 항상 page_view
        events.append(self._create_event(user_id, session_id, current_time, "page_view"))
        current_time = self._add_time_offset(current_time, 2, 15)
        
        # 알림 오픈 (재방문 사용자)
        if random.random() < probs["notification_open"]:
            events.append(self._create_event(user_id, session_id, current_time, "notification_open"))
            current_time = self._add_time_offset(current_time, 1, 5)
        
        # 2. 검색 (45%)
        if random.random() < probs["search"]:
            events.append(self._create_event(user_id, session_id, current_time, "search"))
            current_time = self._add_time_offset(current_time, 3, 30)
        
        # 3. 상품 조회 (70%)
        if random.random() < probs["view_product"]:
            # 여러 상품 조회 가능
            num_products = random.choices([1, 2, 3, 4, 5], weights=[0.3, 0.3, 0.2, 0.15, 0.05])[0]
            for _ in range(num_products):
                events.append(self._create_event(user_id, session_id, current_time, "view_product"))
                current_time = self._add_time_offset(current_time, 20, 120)
                
                # 리뷰 보기 (35%)
                if random.random() < probs["view_review"]:
                    events.append(self._create_event(user_id, session_id, current_time, "view_review"))
                    current_time = self._add_time_offset(current_time, 15, 60)
                
                # 상품 비교 (10%)
                if random.random() < probs["compare_product"]:
                    events.append(self._create_event(user_id, session_id, current_time, "compare_product"))
                    current_time = self._add_time_offset(current_time, 30, 90)
                
                # 번들 보기 (8%)
                if random.random() < probs["bundle_view"]:
                    events.append(self._create_event(user_id, session_id, current_time, "bundle_view"))
                    current_time = self._add_time_offset(current_time, 10, 30)
            
            # 위시리스트 추가 (15%)
            if random.random() < probs["wishlist_add"]:
                events.append(self._create_event(user_id, session_id, current_time, "wishlist_add"))
                current_time = self._add_time_offset(current_time, 2, 10)
            
            # 4. 장바구니 추가 (25%)
            if random.random() < probs["add_to_cart"]:
                events.append(self._create_event(user_id, session_id, current_time, "add_to_cart"))
                current_time = self._add_time_offset(current_time, 5, 30)
                
                # 장바구니에서 제거 (8%)
                if random.random() < probs["remove_from_cart"]:
                    events.append(self._create_event(user_id, session_id, current_time, "remove_from_cart"))
                    current_time = self._add_time_offset(current_time, 3, 15)
                
                # 쿠폰 적용 (12%)
                if random.random() < probs["apply_coupon"]:
                    events.append(self._create_event(user_id, session_id, current_time, "apply_coupon"))
                    current_time = self._add_time_offset(current_time, 10, 60)
                
                # 5. 결제 시작 (18%)
                if random.random() < probs["begin_checkout"]:
                    events.append(self._create_event(user_id, session_id, current_time, "begin_checkout"))
                    current_time = self._add_time_offset(current_time, 30, 180)
                    
                    # 6. 구매 완료 (8%)
                    if random.random() < probs["purchase"]:
                        events.append(self._create_event(user_id, session_id, current_time, "purchase"))
                        current_time = self._add_time_offset(current_time, 1, 5)
                        
                        # 재주문 기능 사용 (5%)
                        if random.random() < probs["reorder"]:
                            events.append(self._create_event(user_id, session_id, current_time, "reorder"))
        
        # 환불 요청 (독립 이벤트, 2%)
        if random.random() < probs["refund_request"]:
            events.append(self._create_event(user_id, session_id, current_time, "refund_request"))
        
        # 시간순 정렬
        events.sort(key=lambda e: e.event_time)
        return events
