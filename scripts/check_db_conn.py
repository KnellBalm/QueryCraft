import psycopg2
from backend.config.db import PostgresEnv

def test_conn(user, password, host, db):
    try:
        dsn = f"host={host} port=5432 user={user} password={password} dbname={db}"
        print(f"Testing {user}@{host}/{db} ...")
        conn = psycopg2.connect(dsn)
        print("✅ SUCCESS!")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

configs = [
    ("postgres", "querycraft", "172.17.0.1", "postgres"),
    ("pa_lab", "pa_lab", "172.17.0.1", "pa_lab"),
    ("postgres", "querycraft", "localhost", "postgres"),
    ("pa_lab", "pa_lab", "localhost", "pa_lab"),
    ("postgres", "querycraft", "192.168.101.224", "postgres"),
]

for u, p, h, d in configs:
    if test_conn(u, p, h, d):
        break
