import psycopg2
import sys

passwords = ["querycraft", "pa_lab", "postgres", "querycraft1!", "querycraft!", "QueryCraft!", "password", "1234", "admin"]
users = ["postgres", "pa_lab", "admin"]

for user in users:
    for password in passwords:
        try:
            dsn = f"host=localhost port=5432 user={user} password={password} dbname={user if user != 'admin' else 'postgres'}"
            conn = psycopg2.connect(dsn, connect_timeout=1)
            print(f"✅ SUCCESS: {user} / {password}")
            conn.close()
            sys.exit(0)
        except Exception as e:
            msg = str(e).split('\n')[0]
            if "authentication failed" in msg:
                continue
            else:
                print(f"❌ Error for {user}/{password}: {msg}")
print("❌ All attempts failed.")
