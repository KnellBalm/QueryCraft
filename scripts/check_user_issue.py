import sys
import os

# PYTHONPATH 설정
sys.path.append(os.getcwd())

from backend.services.database import postgres_connection

def check_user_stats(email):
    with postgres_connection() as pg:
        user = pg.fetch_df("SELECT id, email, xp, level, is_admin FROM public.users WHERE email = %s", [email])
        if user.empty:
            print(f"User {email} not found")
            return
        
        user_id = user.iloc[0]['id']
        print(f"User Info: {user.to_dict('records')[0]}")
        
        # 최근 제출 기록 확인
        subs = pg.fetch_df("""
            SELECT id, problem_id, is_correct, submitted_at, feedback 
            FROM public.submissions 
            WHERE user_id = %s 
            ORDER BY submitted_at DESC 
            LIMIT 5
        """, [user_id])
        print(f"\nRecent Submissions for {user_id}:")
        print(subs)

if __name__ == "__main__":
    email = "naca11@naver.com"
    check_user_stats(email)
