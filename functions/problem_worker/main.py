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

# 환경 변수
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


def get_supabase_client():
    """Supabase 클라이언트 (Cloud Functions용)"""
    from supabase import create_client
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def get_gemini_client(purpose: str = "problem") -> Tuple:
    """용도별 Gemini 클라이언트"""
    from google import genai
    
    models = {
        "problem": os.getenv("GEMINI_MODEL_PROBLEM", "gemini-2.5-flash"),
        "tips": os.getenv("GEMINI_MODEL_TIPS", "gemini-2.5-flash-lite"),
    }
    
    client = genai.Client(api_key=GEMINI_API_KEY)
    return client, models.get(purpose, "gemini-2.5-flash")


def generate_problems_for_date(target_date: date, data_type: str = "pa") -> dict:
    """특정 날짜의 문제 생성"""
    start_time = time.time()
    client, model = get_gemini_client("problem")
    supabase = get_supabase_client()
    
    try:
        # 1. 데이터 요약 생성 (간단히)
        data_summary = f"Date: {target_date}, Type: {data_type}"
        
        # 2. Gemini로 문제 생성
        prompt = f"""
        Create 3 SQL practice problems for {data_type} data analysis.
        Date: {target_date}
        
        Return JSON array with format:
        [
            {{
                "title": "Problem Title",
                "difficulty": "easy|medium|hard",
                "description": "Problem description",
                "initial_sql": "SELECT ",
                "answer_sql": "SELECT ...",
                "hints": ["hint1", "hint2"]
            }}
        ]
        """
        
        response = client.models.generate_content(
            model=model,
            contents=prompt
        )
        
        # 3. 결과 파싱
        text = response.text
        # JSON 추출
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        
        problems = json.loads(text.strip())
        
        # 4. Supabase에 저장
        for i, p in enumerate(problems):
            supabase.table("problems").upsert({
                "problem_date": str(target_date),
                "data_type": data_type,
                "set_index": 0,
                "difficulty": p.get("difficulty"),
                "title": p.get("title"),
                "description": p.get("description"),
                "initial_sql": p.get("initial_sql"),
                "answer_sql": p.get("answer_sql"),
                "hints": p.get("hints"),
            }).execute()
        
        # 5. 로그 기록
        duration_ms = int((time.time() - start_time) * 1000)
        supabase.table("worker_logs").insert({
            "job_type": f"problem_generation_{data_type}",
            "status": "success",
            "model_used": model,
            "duration_ms": duration_ms,
            "result_count": len(problems),
        }).execute()
        
        return {
            "success": True,
            "count": len(problems),
            "model": model,
            "duration_ms": duration_ms
        }
        
    except Exception as e:
        # 에러 로그
        try:
            supabase.table("worker_logs").insert({
                "job_type": f"problem_generation_{data_type}",
                "status": "error",
                "model_used": model,
                "error_message": str(e),
            }).execute()
        except:
            pass
        
        return {
            "success": False,
            "error": str(e)
        }


# Cloud Functions 엔트리포인트
if IN_CLOUD_FUNCTIONS:
    @functions_framework.http
    def generate_problems(request):
        """HTTP 트리거 엔드포인트"""
        today = date.today()
        
        # PA 문제 생성
        pa_result = generate_problems_for_date(today, "pa")
        
        # Stream 문제 생성
        stream_result = generate_problems_for_date(today, "stream")
        
        return {
            "date": str(today),
            "pa": pa_result,
            "stream": stream_result
        }


# 로컬 테스트용
if __name__ == "__main__":
    result = generate_problems_for_date(date.today(), "pa")
    print(json.dumps(result, indent=2))
