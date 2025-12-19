# services/pa_submit.py

def submit_pa(problem_id: str, sql_text: str, note: str | None):
    # 1. SQL 실행
    result_df = run_sql(sql_text)

    # 2. 정답 결과와 비교
    is_correct, diff = compare_with_answer(problem_id, result_df)

    # 3. Gemini 채점
    feedback = call_gemini_review(
        problem_id=problem_id,
        sql_text=sql_text,
        is_correct=is_correct,
        diff=diff,
        note=note,
    )

    # 4. DB 저장
    save_submission(
        problem_id=problem_id,
        sql_text=sql_text,
        is_correct=is_correct,
        feedback=feedback,
    )

    return is_correct, feedback
