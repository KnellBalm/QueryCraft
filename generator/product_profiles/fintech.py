# generator/product_profiles/fintech.py
"""
Fintech Product Profile
금융 서비스 플랫폼 - 트랜잭션/보안 중심
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import List

from .base import BaseProductProfile, Event


class FintechProfile(BaseProductProfile):
    """핀테크 프로필 - 금융 거래/KYC/보안"""
    
    product_type = "fintech"
    
    def generate_session_events(
        self, 
        user_id: str, 
        session_id: str, 
        base_time: datetime
    ) -> List[Event]:
        """
        핀테크 세션 이벤트 생성
        - 기본: login → account_view → balance_check
        - 거래: transfer_attempt → success/fail
        - 결제: card_payment
        - 고급: investment_view, loan_apply
        - 보안: kyc_submit, fraud_alert_view
        """
        events = []
        current_time = base_time
        probs = self.probabilities
        
        # 1. 로그인 (항상)
        events.append(self._create_event(user_id, session_id, current_time, "login"))
        current_time = self._add_time_offset(current_time, 3, 15)
        
        # 2. 계좌 조회 (95%)
        if random.random() < probs["account_view"]:
            events.append(self._create_event(user_id, session_id, current_time, "account_view"))
            current_time = self._add_time_offset(current_time, 10, 60)
        
        # 3. 잔액 확인 (80%)
        if random.random() < probs["balance_check"]:
            # 여러 계좌 확인 가능
            num_checks = random.choices([1, 2, 3], weights=[0.6, 0.3, 0.1])[0]
            for _ in range(num_checks):
                events.append(self._create_event(user_id, session_id, current_time, "balance_check"))
                current_time = self._add_time_offset(current_time, 5, 20)
        
        # 4. 송금 시도 (30%)
        if random.random() < probs["transfer_attempt"]:
            events.append(self._create_event(user_id, session_id, current_time, "transfer_attempt"))
            current_time = self._add_time_offset(current_time, 30, 120)  # 입력 시간
            
            # 성공/실패 결정 (83% 성공, 17% 실패)
            if random.random() < 0.83:
                events.append(self._create_event(user_id, session_id, current_time, "transfer_success"))
            else:
                events.append(self._create_event(user_id, session_id, current_time, "transfer_fail"))
                # 실패 후 재시도 (50%)
                if random.random() < 0.5:
                    current_time = self._add_time_offset(current_time, 10, 60)
                    events.append(self._create_event(user_id, session_id, current_time, "transfer_attempt"))
                    current_time = self._add_time_offset(current_time, 15, 60)
                    if random.random() < 0.9:  # 재시도는 성공 확률 높음
                        events.append(self._create_event(user_id, session_id, current_time, "transfer_success"))
                    else:
                        events.append(self._create_event(user_id, session_id, current_time, "transfer_fail"))
            
            current_time = self._add_time_offset(current_time, 5, 30)
        
        # 5. 카드 결제 (20%)
        if random.random() < probs["card_payment"]:
            num_payments = random.choices([1, 2, 3], weights=[0.7, 0.2, 0.1])[0]
            for _ in range(num_payments):
                events.append(self._create_event(user_id, session_id, current_time, "card_payment"))
                current_time = self._add_time_offset(current_time, 10, 60)
            
            # 취소요청 (1%)
            if random.random() < probs["chargeback"]:
                events.append(self._create_event(user_id, session_id, current_time, "chargeback"))
                current_time = self._add_time_offset(current_time, 60, 300)
        
        # 6. 투자 조회 (18%)
        if random.random() < probs["investment_view"]:
            num_views = random.choices([1, 2, 3, 5], weights=[0.4, 0.3, 0.2, 0.1])[0]
            for _ in range(num_views):
                events.append(self._create_event(user_id, session_id, current_time, "investment_view"))
                current_time = self._add_time_offset(current_time, 30, 180)
        
        # 7. 대출 신청 (5%)
        if random.random() < probs["loan_apply"]:
            events.append(self._create_event(user_id, session_id, current_time, "loan_apply"))
            current_time = self._add_time_offset(current_time, 300, 900)  # 신청서 작성
        
        # 8. KYC 제출 (15% - 신규 사용자)
        if random.random() < probs["kyc_submit"]:
            events.append(self._create_event(user_id, session_id, current_time, "kyc_submit"))
            current_time = self._add_time_offset(current_time, 120, 600)
        
        # 9. 사기 알림 조회 (2%)
        if random.random() < probs["fraud_alert_view"]:
            events.append(self._create_event(user_id, session_id, current_time, "fraud_alert_view"))
        
        # 시간순 정렬
        events.sort(key=lambda e: e.event_time)
        return events
