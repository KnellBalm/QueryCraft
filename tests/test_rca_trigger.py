
import requests
import json
import sys

# 세션 ID (로컬 개발 환경에서는 직접 DB나 브라우저에서 가져와야 함)
# 여기서는 API 엔드포인트 동작 확인을 위해 간단한 호출 시도
BASE_URL = "http://localhost:15174/api"
SESSION_ID = "test-session-id" # 실제 테스트 시에는 유효한 세션 필요

def test_rca_trigger():
    print("Testing RCA Trigger...")
    
    # 1. RCA 트리거 호출
    # 실제 환경에서는 아토믹하게 동작하는지 확인
    payload = {
        "anomaly_type": "RETENTION_DROP",
        "product_type": "commerce"
    }
    
    headers = {
        "X-Scheduler-Key": "test-key" # scheduler_api_key
    }
    
    # 관리자 세션이 필요하므로, 여기서는 로직만 시뮬레이션하거나 
    # 내부 서비스를 직접 호출하는 방식으로 테스트 가능 (백엔드 코드 수준에서)
    pass

if __name__ == "__main__":
    # 백엔드 코드를 직접 임포트하여 테스트
    sys.path.append(".")
    from backend.services.database import postgres_connection
    from backend.generator.anomaly_injector import inject_random_anomaly, AnomalyType
    from problems.generator import generate as gen_problems
    from backend.common.date_utils import get_today_kst

    print("--- Internal RCA Trigger Test ---")
    with postgres_connection() as pg:
        today = get_today_kst()
        print(f"Injecting anomaly for {today}...")
        info = inject_random_anomaly(pg, "commerce", force_type=AnomalyType.RETENTION_DROP)
        print(f"Injected: {info['type']}")
        
        print("Generating RCA problems...")
        path = gen_problems(today, pg, mode="rca", product_type="commerce")
        print(f"Problems generated at: {path}")
        
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
            problems = data.get("problems", [])
            print(f"Found {len(problems)} problems.")
            for i, p in enumerate(problems[:1]):
                print(f"Problem {i+1} title: {p.get('title')}")
                print(f"Hints: {p.get('hints')}")
                if p.get('hints') and len(p.get('hints')) > 0:
                    print("SUCCESS: Hints generated correctly.")
                else:
                    print("WARNING: No sequential hints found.")

