from backend.services.db_init import init_database
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)

def manual_init():
    print("Starting manual database initialization...")
    success, error = init_database()
    if success:
        print("SUCCESS: Database initialized")
    else:
        print(f"FAILED: {error}")

if __name__ == "__main__":
    manual_init()
