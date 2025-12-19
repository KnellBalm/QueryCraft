CREATE TABLE IF NOT EXISTS stream_submissions (
    session_date DATE,
    problem_id TEXT,
    submitted_at TIMESTAMP,
    PRIMARY KEY (session_date, problem_id)
);
