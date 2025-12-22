// frontend/src/pages/Workspace.tsx
import { useEffect, useState, useCallback } from 'react';
import { SQLEditor } from '../components/SQLEditor';
import { TableSchema } from '../components/TableSchema';
import { ResultTable } from '../components/ResultTable';
import { problemsApi, sqlApi } from '../api/client';
import type { Problem, TableSchema as Schema, SQLExecuteResponse, SubmitResponse } from '../types';
import './Workspace.css';

interface WorkspaceProps {
    dataType: 'pa' | 'stream';
}

export function Workspace({ dataType }: WorkspaceProps) {
    const [problems, setProblems] = useState<Problem[]>([]);
    const [selectedProblem, setSelectedProblem] = useState<Problem | null>(null);
    const [tables, setTables] = useState<Schema[]>([]);
    const [sql, setSql] = useState('');
    const [result, setResult] = useState<SQLExecuteResponse | null>(null);
    const [submitResult, setSubmitResult] = useState<SubmitResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [activeTab, setActiveTab] = useState<'problem' | 'schema'>('problem');

    // 데이터 로드
    useEffect(() => {
        async function load() {
            try {
                const [problemsRes, schemaRes] = await Promise.all([
                    problemsApi.list(dataType),
                    problemsApi.schema(dataType),
                ]);
                setProblems(problemsRes.data.problems);
                setTables(schemaRes.data);
                if (problemsRes.data.problems.length > 0) {
                    setSelectedProblem(problemsRes.data.problems[0]);
                }
            } catch (error) {
                console.error('Failed to load data:', error);
            }
        }
        load();
    }, [dataType]);

    // SQL 실행
    const handleExecute = useCallback(async () => {
        if (!sql.trim()) return;
        setLoading(true);
        setSubmitResult(null);
        try {
            const res = await sqlApi.execute(sql);
            setResult(res.data);
        } catch (error: any) {
            setResult({ success: false, error: error.message });
        }
        setLoading(false);
    }, [sql]);

    // 제출
    const handleSubmit = useCallback(async () => {
        if (!sql.trim() || !selectedProblem) return;
        setLoading(true);
        try {
            const res = await sqlApi.submit(selectedProblem.problem_id, sql);
            setSubmitResult(res.data);
        } catch (error: any) {
            setSubmitResult({ is_correct: false, feedback: error.message });
        }
        setLoading(false);
    }, [sql, selectedProblem]);

    const difficultyIcon = {
        easy: '🟢',
        medium: '🟡',
        hard: '🔴',
    };

    return (
        <div className="workspace">
            {/* 좌측 패널 */}
            <div className="left-panel">
                <div className="panel-tabs">
                    <button
                        className={activeTab === 'problem' ? 'active' : ''}
                        onClick={() => setActiveTab('problem')}
                    >
                        📌 문제
                    </button>
                    <button
                        className={activeTab === 'schema' ? 'active' : ''}
                        onClick={() => setActiveTab('schema')}
                    >
                        📋 스키마
                    </button>
                </div>

                {activeTab === 'problem' ? (
                    <div className="problem-panel">
                        {/* 문제 목록 */}
                        <div className="problem-list">
                            {problems.map((p) => (
                                <button
                                    key={p.problem_id}
                                    className={`problem-item ${selectedProblem?.problem_id === p.problem_id ? 'active' : ''}`}
                                    onClick={() => setSelectedProblem(p)}
                                >
                                    <span className="status">
                                        {p.is_completed ? (p.is_correct ? '✅' : '❌') : '⬜'}
                                    </span>
                                    <span className="difficulty">{difficultyIcon[p.difficulty]}</span>
                                    <span className="id">{p.problem_id}</span>
                                </button>
                            ))}
                        </div>

                        {/* 문제 상세 */}
                        {selectedProblem && (
                            <div className="problem-detail">
                                <div className="problem-header">
                                    <span className="difficulty-badge">{difficultyIcon[selectedProblem.difficulty]} {selectedProblem.difficulty}</span>
                                    {selectedProblem.requester && (
                                        <span className="requester">📧 {selectedProblem.requester}</span>
                                    )}
                                </div>
                                <h2>{selectedProblem.problem_id}</h2>
                                <div className="question">{selectedProblem.question}</div>
                                {selectedProblem.context && (
                                    <details className="context">
                                        <summary>💡 배경</summary>
                                        <p>{selectedProblem.context}</p>
                                    </details>
                                )}
                                {selectedProblem.expected_columns && (
                                    <div className="expected-cols">
                                        <strong>결과 컬럼:</strong>
                                        <code>{selectedProblem.expected_columns.join(', ')}</code>
                                    </div>
                                )}
                                {selectedProblem.hint && (
                                    <details className="hint">
                                        <summary>💬 힌트</summary>
                                        <p>{selectedProblem.hint}</p>
                                    </details>
                                )}
                            </div>
                        )}
                    </div>
                ) : (
                    <TableSchema tables={tables} />
                )}
            </div>

            {/* 우측 패널 */}
            <div className="right-panel">
                {/* SQL 에디터 */}
                <div className="editor-section">
                    <div className="editor-header">
                        <span>💻 SQL</span>
                        <span className="shortcut">Ctrl+Enter로 실행</span>
                    </div>
                    <SQLEditor
                        value={sql}
                        onChange={setSql}
                        onExecute={handleExecute}
                        height="200px"
                    />
                    <div className="editor-actions">
                        <button onClick={handleExecute} disabled={loading} className="btn-execute">
                            {loading ? '⏳' : '▶️'} 테스트
                        </button>
                        <button onClick={handleSubmit} disabled={loading || !selectedProblem} className="btn-submit">
                            🚀 제출
                        </button>
                    </div>
                </div>

                {/* 결과 / 피드백 */}
                <div className="result-section">
                    {submitResult && (
                        <div className={`submit-result ${submitResult.is_correct ? 'correct' : 'wrong'}`}>
                            <div className="result-icon">
                                {submitResult.is_correct ? '✅ 정답!' : '❌ 오답'}
                            </div>
                            <div className="feedback">{submitResult.feedback}</div>
                        </div>
                    )}

                    {result && result.success && result.data && (
                        <ResultTable
                            columns={result.columns || []}
                            data={result.data}
                            executionTime={result.execution_time_ms}
                        />
                    )}

                    {result && !result.success && (
                        <div className="error-result">
                            ❌ {result.error}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
