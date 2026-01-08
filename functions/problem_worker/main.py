# functions/problem_worker/main.py
"""Cloud Functions - 문제 생성 워커
매일 KST 01:00에 Cloud Scheduler가 호출
"""
import os
import json
import time
from datetime import date
from typing import Tuple

# Cloud Functions 환경에서는 functions-framework 사용
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
def generate_problems(request):
    """백엔드 API를 호출하는 프록시 엔드포인트"""
    if not SCHEDULER_API_KEY:
        return {"success": False, "error": "SCHEDULER_API_KEY is not configured"}, 500
        
    url = f"{BACKEND_URL}/admin/trigger/daily-generation"
    headers = {
        "X-Scheduler-Key": SCHEDULER_API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, headers=headers, timeout=300) # 5분 타임아웃
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {
            "success": False, 
            "error": str(e),
            "backend_url": url
        }, 500


# 로컬 테스트용
if __name__ == "__main__":
    result = generate_problems_for_date(date.today(), "pa")
    print(json.dumps(result, indent=2))
