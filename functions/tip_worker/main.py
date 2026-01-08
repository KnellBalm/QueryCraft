# functions/tip_worker/main.py
"""Cloud Functions - 오늘의 팁 생성 워커
경량 모델 사용 (gemini-2.5-flash-lite)
"""
import os
import time
from datetime import date

try:
    import functions_framework
    IN_CLOUD_FUNCTIONS = True
except ImportError:
    IN_CLOUD_FUNCTIONS = False

import requests

# 환경 변수
BACKEND_URL = os.getenv("BACKEND_URL", "https://query-craft-backend-53ngedkhia-uc.a.run.app")
SCHEDULER_API_KEY = os.getenv("SCHEDULER_API_KEY")

@functions_framework.http
def generate_tip(request):
    """백엔드 API를 호출하여 오늘의 팁을 생성하는 프록시"""
    if not SCHEDULER_API_KEY:
        return {"success": False, "error": "SCHEDULER_API_KEY is not configured"}, 500
        
    url = f"{BACKEND_URL}/admin/trigger/daily-tip"
    headers = {
        "X-Scheduler-Key": SCHEDULER_API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, headers=headers, timeout=60)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {
            "success": False, 
            "error": str(e),
            "backend_url": url
        }, 500
