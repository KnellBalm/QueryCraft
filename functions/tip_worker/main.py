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

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


def get_supabase_client():
    from supabase import create_client
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def generate_daily_tip(target_date: date) -> dict:
    """오늘의 SQL 팁 생성"""
    from google import genai
    
    start_time = time.time()
    model = os.getenv("GEMINI_MODEL_TIPS", "gemini-2.5-flash-lite")
    client = genai.Client(api_key=GEMINI_API_KEY)
    supabase = get_supabase_client()
    
    try:
        prompt = """
        Generate a single SQL tip of the day in Korean.
        Keep it short (2-3 sentences), practical, and beginner-friendly.
        Topics: window functions, joins, aggregations, date functions, etc.
        
        Format:
        💡 [제목]
        [설명]
        """
        
        response = client.models.generate_content(
            model=model,
            contents=prompt
        )
        
        tip_content = response.text.strip()
        
        # Supabase에 저장
        supabase.table("daily_tips").upsert({
            "tip_date": str(target_date),
            "content": tip_content,
            "category": "sql",
            "model_used": model,
        }).execute()
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        supabase.table("worker_logs").insert({
            "job_type": "tip_generation",
            "status": "success",
            "model_used": model,
            "duration_ms": duration_ms,
            "result_count": 1,
        }).execute()
        
        return {
            "success": True,
            "tip": tip_content,
            "model": model,
            "duration_ms": duration_ms
        }
        
    except Exception as e:
        try:
            supabase.table("worker_logs").insert({
                "job_type": "tip_generation",
                "status": "error",
                "model_used": model,
                "error_message": str(e),
            }).execute()
        except:
            pass
        
        return {"success": False, "error": str(e)}


if IN_CLOUD_FUNCTIONS:
    @functions_framework.http
    def generate_tip(request):
        return generate_daily_tip(date.today())


if __name__ == "__main__":
    import json
    result = generate_daily_tip(date.today())
    print(json.dumps(result, indent=2, ensure_ascii=False))
