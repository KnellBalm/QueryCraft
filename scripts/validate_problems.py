import json
from datetime import date
from backend.services.problem_service import get_problems
from backend.schemas.problem import Problem

def validate():
    today = date(2026, 1, 13)
    print(f"Testing for date: {today}")
    
    for dt in ["pa", "stream"]:
        print(f"\n--- Checking {dt} ---")
        # Test with set_index 0, 1, 2
        for s_idx in [0, 1, 2]:
            print(f"Testing set_index {s_idx}...")
            # We can't easily mock user session here, but get_problems uses target_date
            problems = get_problems(data_type=dt, target_date=today)
            print(f"Found {len(problems)} problems")
            if problems:
                print(f"First problem ID: {problems[0].problem_id}")
            else:
                print("No problems found!")

if __name__ == "__main__":
    validate()
