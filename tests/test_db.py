
from backend.services.database import postgres_connection
try:
    with postgres_connection() as pg:
        print("DB Connection Success")
except Exception as e:
    print(f"DB Connection Failed: {e}")
