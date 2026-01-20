// frontend/src/types/index.ts

export interface TableColumn {
    column_name: string;
    data_type: string;
}

export interface TableSchema {
    table_name: string;
    columns: TableColumn[];
    row_count?: number;
}

export interface Problem {
    problem_id: string;
    title?: string;
    data_type?: string;
    problem_type?: string;
    difficulty: 'easy' | 'medium' | 'hard';
    topic: string;
    requester?: string;
    question: string;
    context?: string;
    expected_description?: string;
    expected_columns?: string[];
    sort_keys?: string[];
    hint?: string;
    hints?: string[];
    is_completed?: boolean;
    is_correct?: boolean;
}

export interface DatasetMetadata {
    company_name: string;
    company_description: string;
    product_type: string;
    north_star?: string;
    key_metrics?: string[];
}

export interface ProblemListResponse {
    date: string;
    data_type: string;
    problems: Problem[];
    total: number;
    completed: number;
    metadata?: DatasetMetadata;
}

export interface SQLExecuteResponse {
    success: boolean;
    columns?: string[];
    data?: Record<string, any>[];
    row_count?: number;
    execution_time_ms?: number;
    error?: string;
}

export interface SubmitResponse {
    is_correct: boolean;
    feedback: string;
    execution_time_ms?: number;
    diff?: string;
}

export interface UserStats {
    streak: number;
    max_streak: number;
    level: string;
    total_solved: number;
    correct: number;
    accuracy: number;
    next_level_threshold: number;
    score?: number;
    level_progress?: number;
}
