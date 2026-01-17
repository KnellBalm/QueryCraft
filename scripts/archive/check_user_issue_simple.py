import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

def get_connection():
    return psycopg2.connect(
        host=os.getenv("PG_HOST"),
        port=os.getenv("PG_PORT", 25432),
        user=os.getenv("PG_USER"),
        password=os.getenv("PG_PASSWORD"),
        dbname=os.getenv("PG_DB")
    )

def check_user_stats(email):
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT id, email, xp, level, is_admin FROM public.users WHERE email = %s", (email,))
    user = cur.fetchone()
    
    if not user:
        print(f"User {email} not found")
        return
    
    user_id, email, xp, level, is_admin = user
    print(f"User Info: ID={user_id}, Email={email}, XP={xp}, Level={level}, Admin={is_admin}")
    
    # 최근 제출 기록 확인
    cur.execute("""
        SELECT id, problem_id, is_correct, submitted_at, feedback 
        FROM public.submissions 
        WHERE user_id = %s 
        ORDER BY id DESC 
        LIMIT 5
    """, (user_id,))
    subs = cur.fetchall()
    print(f"\nRecent Submissions for {user_id}:")
    for s in subs:
        print(s)
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    email = "naca11@naver.com"
    check_user_stats(email)
