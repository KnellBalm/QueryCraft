import os
import psycopg2
from dotenv import load_dotenv

def get_users():
    dsn = "postgresql://zokr:8633@192.168.101.224:25432/da"
    conn = psycopg2.connect(dsn)
    cur = conn.cursor()
    cur.execute("SELECT email, name, is_admin FROM public.users")
    rows = cur.fetchall()
    for row in rows:
        print(f"Email: {row[0]}, Name: {row[1]}, Admin: {row[2]}")
    cur.close()
    conn.close()

if __name__ == "__main__":
    get_users()
