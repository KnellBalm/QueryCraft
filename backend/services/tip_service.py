
import os
from datetime import date
from backend.services.database import postgres_connection
from backend.services.db_logger import db_log, LogCategory, LogLevel
from problems.gemini import call_gemini_json, get_model

def generate_tip_of_the_day(today: date) -> dict:
    """오늘의 SQL 팁 생성 및 DB 저장"""
    try:
        model_name = os.getenv("GEMINI_MODEL_TIPS", "gemini-2.0-flash-lite")
        
        prompt = """
        Generate a single SQL tip of the day in Korean.
        Keep it short (2-3 sentences), practical, and professional.
        Topics: window functions, performance optimization, data analysis patterns, etc.
        
        Return JSON format:
        {
            "title": "Tip Title",
            "content": "Detailed explanation...",
            "category": "performance|syntax|analysis"
        }
        """
        
        from problems.gemini import GEMINI_API_KEY
        from google import genai
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config={"response_mime_type": "application/json"}
        )
        
        import json
        tip_data = json.loads(response.text.strip())
        
        title = tip_data.get("title", "오늘의 SQL 팁")
        content = tip_data.get("content", "")
        category = tip_data.get("category", "sql")
        
        full_content = f"💡 {title}\n{content}"
        
        with postgres_connection() as pg:
            pg.execute("""
                INSERT INTO public.daily_tips (tip_date, content, category, model_used)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (tip_date) DO UPDATE SET
                    content = EXCLUDED.content,
                    category = EXCLUDED.category,
                    model_used = EXCLUDED.model_used
            """, [today, full_content, category, model_name])
            
        return {"success": True, "tip": full_content}
        
    except Exception as e:
        db_log(LogCategory.SYSTEM, f"Tip generation failed: {e}", LogLevel.ERROR, "tip_service")
        return {"success": False, "error": str(e)}
