import { useState, useCallback, useRef } from 'react';
import { sqlApi } from '../api/client';
import { analytics } from '../services/analytics';
import type { Problem, TableSchema as Schema, SQLExecuteResponse } from '../types';

interface UseSQLExecutionReturn {
  sql: string;
  setSql: (sql: string) => void;
  result: SQLExecuteResponse | null;
  loading: boolean;
  handleExecute: () => Promise<void>;
}

export function useSQLExecution(
  selectedProblem: Problem | undefined,
  _tables: Schema[],
  _dataType: string
): UseSQLExecutionReturn {
  const [sql, setSql] = useState('');
  const [result, setResult] = useState<SQLExecuteResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const lastAttemptedRef = useRef<string | null>(null);

  const handleExecute = useCallback(async () => {
    if (!sql.trim()) return;
    setLoading(true);

    // 첫 실행/타이핑 시 시도로 기록
    if (selectedProblem && lastAttemptedRef.current !== selectedProblem.problem_id) {
      analytics.problemAttempted(selectedProblem.problem_id, selectedProblem.difficulty);
      lastAttemptedRef.current = selectedProblem.problem_id;
    }

    try {
      const res = await sqlApi.execute(sql);
      setResult(res.data);
      analytics.sqlExecuted(selectedProblem?.problem_id || 'unknown', {
        sql,
        hasError: !res.data.success,
        errorMessage: res.data.error,
        dbEngine: 'postgres'
      });
    } catch (error: any) {
      setResult({ success: false, error: error.message });
      analytics.sqlExecuted(selectedProblem?.problem_id || 'unknown', {
        sql,
        hasError: true,
        errorType: 'runtime',
        errorMessage: error.message,
        dbEngine: 'postgres'
      });
    }
    setLoading(false);
  }, [sql, selectedProblem]);

  return {
    sql,
    setSql,
    result,
    loading,
    handleExecute
  };
}
