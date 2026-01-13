import pytz
from datetime import datetime, date

def get_today_kst() -> date:
    """한국 시간(KST) 기준 오늘 날짜 반환"""
    kst = pytz.timezone('Asia/Seoul')
    return datetime.now(kst).date()

def get_now_kst() -> datetime:
    """한국 시간(KST) 기준 현재 일시 반환"""
    kst = pytz.timezone('Asia/Seoul')
    return datetime.now(kst)
