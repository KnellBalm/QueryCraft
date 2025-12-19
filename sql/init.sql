CREATE TABLE IF NOT EXISTS daily_sessions (
    session_date DATE PRIMARY KEY,
    problem_set_path TEXT NOT NULL,
    generated_at TIMESTAMP NOT NULL,
    started_at TIMESTAMP,
    finished_at TIMESTAMP,
    status TEXT CHECK (status IN ('GENERATED','STARTED','FINISHED','SKIPPED')) NOT NULL
);

CREATE TABLE IF NOT EXISTS submissions (
    session_date DATE NOT NULL,
    problem_id TEXT NOT NULL,
    difficulty TEXT NOT NULL,
    submitted_at TIMESTAMP NOT NULL,
    is_correct BOOLEAN NOT NULL,
    error_category TEXT,
    error_type TEXT,
    error_message TEXT,
    PRIMARY KEY (session_date, problem_id)
);
