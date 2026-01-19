
import os
from datetime import datetime

# Simulating the fixed behavior to verify against the schema I found via MCP
# Table: public.submissions
# Columns: session_date (date, NOT NULL), problem_id (text, NOT NULL), data_type (text), 
#          submitted_sql (text), is_correct (boolean, NOT NULL), note (text), 
#          user_id (text), difficulty (text, NOT NULL), submitted_at (timestamp, NOT NULL),
#          xp_earned (int)

def get_verification_query(user_id, problem_id, is_correct, xp_earned):
    # This matches the new code in grading_service.py
    query = """
    INSERT INTO public.submissions (
        session_date, problem_id, data_type, submitted_sql, 
        is_correct, note, user_id, difficulty, submitted_at, xp_earned
    )
    VALUES ('2026-01-20', %s, 'pa', 'SELECT 1;', %s, 'Verification Test', %s, 'easy', NOW(), %s)
    RETURNING id;
    """
    params = (problem_id, is_correct, user_id, xp_earned)
    return query, params

if __name__ == "__main__":
    # Just printing the query to verify logic
    user_id = "local_b70f550caa204f87"
    problem_id = "2026-01-20_saas_sql_002_easy_set0_pa"
    query, params = get_verification_query(user_id, problem_id, True, 3)
    print("Verification SQL (Simulated):")
    print(query % tuple(f"'{p}'" if isinstance(p, str) else p for p in params))
