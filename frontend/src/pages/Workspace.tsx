// frontend/src/pages/Workspace.tsx
import { useEffect, useState, useCallback, useRef } from 'react';
import { SQLEditor } from '../components/SQLEditor';
import { TableSchema } from '../components/TableSchema';
import { InsightModal } from '../components/InsightModal';
import { ResultPanel } from './Workspace/components/ResultPanel';
import { useTrack } from '../contexts/TrackContext';
import { useProblemCompletion } from '../hooks/useProblemCompletion';
import { problemsApi, sqlApi } from '../api/client';
import { analytics } from '../services/analytics';
import type { Problem, TableSchema as Schema, SQLExecuteResponse, SubmitResponse } from '../types';
import './Workspace.css';

// 간단한 마크다운 변환 (볼드, 코드, 줄바꿈)
function renderMarkdown(text: string | undefined | null) {
    if (!text) return null;
    const html = text
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')  // **bold**
        .replace(/`(.+?)`/g, '<code>$1</code>')            // `code`
        .replace(/\n/g, '<br/>');                          // 줄바꿈
    return <span dangerouslySetInnerHTML={{ __html: html }} />;
}

interface WorkspaceProps {
    dataType: 'pa' | 'stream' | 'rca';
}

export function Workspace({ dataType }: WorkspaceProps) {
    const [problems, setProblems] = useState<Problem[]>([]);
    const [isFetching, setIsFetching] = useState(false);
    const [selectedIndex, setSelectedIndex] = useState(0);
    const [tables, setTables] = useState<Schema[]>([]);
    const [sql, setSql] = useState('');
    const [result, setResult] = useState<SQLExecuteResponse | null>(null);
    const [submitResult, setSubmitResult] = useState<SubmitResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [submitting, setSubmitting] = useState(false);
    const [hint, setHint] = useState<string | null>(null);
    const [activeTab, setActiveTab] = useState<'problem' | 'schema'>('problem');
    const [leftWidth, setLeftWidth] = useState(45);
    const [editorHeightPercent, setEditorHeightPercent] = useState(50); // 기본 50%
    const [metadata, setMetadata] = useState<any>(null); // DatasetMetadata
    const [insightData, setInsightData] = useState<any>(null); // 구조화된 인사이트 데이터
    const [showInsightModal, setShowInsightModal] = useState(false);
    const [insightLoading, setInsightLoading] = useState(false);
    const [translateQuery, setTranslateQuery] = useState('');
    const [translating, setTranslating] = useState(false);

    // AI 도움 기능 (Daily 문제용)
    const [aiHelpUsed, setAiHelpUsed] = useState<{[problemId: string]: boolean}>({});
    const [aiHelpResult, setAiHelpResult] = useState<{type: string; content: string} | null>(null);
    const [aiHelpLoading, setAiHelpLoading] = useState(false);
    const [showAiHelpMenu, setShowAiHelpMenu] = useState(false);

    const resizerRef = useRef<HTMLDivElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);
    const rightPanelRef = useRef<HTMLDivElement>(null);
    const lastAttemptedRef = useRef<string | null>(null);

    const selectedProblem = problems[selectedIndex] || null;
    const { track } = useTrack(); // Future Lab에서만 AI 기능 활성화
    const { completedStatus, updateCompletion, getStatusIcon } = useProblemCompletion(dataType, problems);

    // 데이터 로드
    const loadData = useCallback(async () => {
        setIsFetching(true);
        try {
            const [problemsRes, schemaRes] = await Promise.all([
                problemsApi.list(dataType),
                problemsApi.schema(dataType),
            ]);
            const newProblems = Array.isArray(problemsRes.data.problems) ? problemsRes.data.problems : [];
            setProblems(newProblems);
            setTables(Array.isArray(schemaRes.data) ? schemaRes.data : []);
            setMetadata(problemsRes.data.metadata || null);
            setSelectedIndex(0);
            setSubmitResult(null);
            setResult(null);
            setHint(null);
            setSql('');

            // Completion history loading is now handled by useProblemCompletion hook
        } catch (error) {
            console.error('Failed to load data:', error);
        } finally {
            setIsFetching(false);
        }
    }, [dataType]);

    useEffect(() => {
        loadData();
    }, [loadData]);

    // Analytics: 페이지 로드 및 문제 선택 추적
    useEffect(() => {
        analytics.pageView(dataType === 'pa' ? '/pa-practice' : '/stream', { data_type: dataType });
    }, [dataType]);

    useEffect(() => {
        if (selectedProblem) {
            analytics.problemViewed(selectedProblem.problem_id, {
                difficulty: selectedProblem.difficulty,
                dataType,
                isDaily: dataType === 'pa' || dataType === 'stream',
                topic: selectedProblem.topic
            });
        }
    }, [selectedProblem, dataType]);

    // SQL 실행
    const handleExecute = useCallback(async () => {
        if (!sql.trim()) return;
        setLoading(true);
        setSubmitResult(null);
        setHint(null);

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

    // 제출
    const handleSubmit = useCallback(async () => {
        if (!sql.trim() || !selectedProblem) return;
        setSubmitting(true);
        setSubmitResult(null);
        setHint(null);
        try {
            const res = await sqlApi.submit(selectedProblem.problem_id, sql, dataType);
            setSubmitResult(res.data);

            // Update completion status via hook
            updateCompletion(selectedProblem.problem_id, res.data.is_correct);

            analytics.problemSubmitted(selectedProblem.problem_id, {
                isCorrect: res.data.is_correct,
                difficulty: selectedProblem.difficulty,
                dataType: dataType
            });
        } catch (error: any) {
            setSubmitResult({ is_correct: false, feedback: error.message });
        }
        setSubmitting(false);
    }, [sql, selectedProblem, updateCompletion, dataType]);

    // AI 인사이트
    const handleInsight = useCallback(async () => {
        if (!result?.data || !selectedProblem || !result.success) return;
        setInsightLoading(true);
        setInsightData(null);

        analytics.aiInsightRequested(selectedProblem.problem_id, {
            dataType: dataType,
            resultCount: result.data.length
        });

        try {
            const res = await sqlApi.insight(selectedProblem.problem_id, sql, result.data, dataType);
            setInsightData(res.data);
            setShowInsightModal(true);
        } catch (error: any) {
            console.error('Failed to get AI insight:', error);
            // 에러 시에도 간단한 메시지 표시
            setInsightData({
                key_findings: [],
                insights: [],
                action_items: [],
                suggested_queries: [],
                report_markdown: `# 오류\n\n인사이트 생성 실패: ${error.message}`
            });
            setShowInsightModal(true);
        }
        setInsightLoading(false);
    }, [result, selectedProblem, sql, dataType]);

    // Text-to-SQL
    const handleTranslate = useCallback(async () => {
        if (!translateQuery.trim()) return;
        setTranslating(true);

        analytics.textToSQLRequested(translateQuery, {
            problemId: selectedProblem?.problem_id,
            dataType: dataType
        });

        try {
            const res = await sqlApi.translate(translateQuery, dataType);
            setSql(res.data.sql);
            setTranslateQuery('');
        } catch (error: any) {
            console.error('Translation failed:', error);
        }
        setTranslating(false);
    }, [translateQuery, dataType]);

    // AI 도움 요청 (문제당 1회)
    const handleAiHelp = useCallback(async (helpType: 'hint' | 'solution') => {
        if (!selectedProblem) return;
        if (aiHelpUsed[selectedProblem.problem_id]) return; // 이미 사용됨

        setAiHelpLoading(true);
        setShowAiHelpMenu(false);
        setAiHelpResult(null);

        // 시도 횟수 계산 (completion status에서 확인)
        const attemptCount = completedStatus[selectedProblem.problem_id] ? 1 : 0;

        try {
            const res = await sqlApi.aiHelp(
                selectedProblem.problem_id,
                helpType,
                sql,
                attemptCount,
                dataType
            );
            setAiHelpResult(res.data);

            // 사용 기록 저장
            const newUsed = { ...aiHelpUsed, [selectedProblem.problem_id]: true };
            setAiHelpUsed(newUsed);
            localStorage.setItem(`ai_help_used_${dataType}`, JSON.stringify(newUsed));

            analytics.aiHelpRequested(selectedProblem.problem_id, helpType, {
                difficulty: selectedProblem.difficulty,
                dataType: dataType,
                attemptsBefore: attemptCount
            });
        } catch (error: any) {
            setAiHelpResult({ type: 'error', content: `AI 도움 요청 실패: ${error.message}` });
        }
        setAiHelpLoading(false);
    }, [selectedProblem, aiHelpUsed, sql, completedStatus, dataType]);

    // 좌우 리사이저
    const handleMouseDown = useCallback((e: React.MouseEvent) => {
        e.preventDefault();
        const container = containerRef.current;
        if (!container) return;

        const handleMouseMove = (e: MouseEvent) => {
            const containerRect = container.getBoundingClientRect();
            const newWidth = ((e.clientX - containerRect.left) / containerRect.width) * 100;
            setLeftWidth(Math.min(Math.max(newWidth, 20), 80));
        };

        const handleMouseUp = () => {
            document.removeEventListener('mousemove', handleMouseMove);
            document.removeEventListener('mouseup', handleMouseUp);
        };

        document.addEventListener('mousemove', handleMouseMove);
        document.addEventListener('mouseup', handleMouseUp);
    }, []);

    // 상하 리사이저
    const handleMouseDownVertical = useCallback((e: React.MouseEvent) => {
        e.preventDefault();
        const rightPanel = rightPanelRef.current;
        if (!rightPanel) return;

        const handleMouseMove = (e: MouseEvent) => {
            const rightPanelRect = rightPanel.getBoundingClientRect();
            const newHeightPercent = ((e.clientY - rightPanelRect.top) / rightPanelRect.height) * 100;
            setEditorHeightPercent(Math.min(Math.max(newHeightPercent, 20), 80));
        };

        const handleMouseUp = () => {
            document.removeEventListener('mousemove', handleMouseMove);
            document.removeEventListener('mouseup', handleMouseUp);
        };

        document.addEventListener('mousemove', handleMouseMove);
        document.addEventListener('mouseup', handleMouseUp);
    }, []);

    const difficultyIcon: Record<string, string> = {
        easy: '🟢', medium: '🟡', hard: '🔴',
    };

    return (
        <div className="workspace" ref={containerRef}>
            {/* 좌측 패널 */}
            <div className="left-panel" style={{ width: `${leftWidth}%` }}>
                <div className="panel-tabs">
                    <button className={activeTab === 'problem' ? 'active' : ''} onClick={() => { setActiveTab('problem'); analytics.tabChanged('problem', dataType); }}>
                        문제
                    </button>
                    <button className={activeTab === 'schema' ? 'active' : ''} onClick={() => { setActiveTab('schema'); analytics.schemaViewed(dataType); }}>
                        스키마
                    </button>
                </div>

                {activeTab === 'problem' ? (
                    <div className="problem-panel">
                        <div className="problem-list">
                            {Array.isArray(problems) && problems.map((p, idx) => (
                                <button
                                    key={p.problem_id}
                                    className={`problem-item ${selectedIndex === idx ? 'active' : ''}`}
                                    onClick={() => { setSelectedIndex(idx); setSql(''); setSubmitResult(null); setResult(null); setHint(null); }}
                                >
                                    <span className="status">{getStatusIcon(p.problem_id)}</span>
                                    <span className="num">{idx + 1}번</span>
                                    <span className="difficulty">{difficultyIcon[p.difficulty]}</span>
                                </button>
                            ))}
                        </div>

                        {metadata && (
                            <div className="dataset-context">
                                <div className="context-header">
                                    <span className={`company-badge ${dataType === 'rca' ? 'rca' : ''}`}>
                                        {dataType === 'rca' ? '🚨 ANOMALY DETECTION' : 'BUSINESS CONTEXT'}
                                    </span>
                                    <span className="product-type-tag">{metadata.product_type}</span>
                                    {dataType === 'rca' && <span className="rca-tag">Root Cause Analysis</span>}
                                </div>
                                <div className="company-name">{metadata.company_name}</div>
                                <div className="company-desc">{metadata.company_description}</div>

                                {metadata.north_star && (
                                    <div className="kpi-row">
                                        <div className="kpi-item">
                                            <span className="kpi-label">North Star Metric</span>
                                            <span className="kpi-value">✨ {metadata.north_star}</span>
                                        </div>
                                        {metadata.key_metrics && metadata.key_metrics.length > 0 && (
                                            <div className="kpi-item">
                                                <span className="kpi-label">Core KPIs</span>
                                                <span className="kpi-value">📊 {metadata.key_metrics[0]} 등</span>
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        )}

                        {selectedProblem && (
                            <div className="problem-detail">
                                <div className="problem-title">
                                    <span className="problem-number">문제 {selectedIndex + 1}</span>
                                    <span className="difficulty-badge">
                                        {difficultyIcon[selectedProblem.difficulty]} {selectedProblem.difficulty}
                                    </span>
                                </div>

                                {selectedProblem.requester && (
                                    <div className={`slack-message ${dataType === 'rca' ? 'rca' : ''}`}>
                                        <div className="slack-header">
                                            <span className="slack-avatar">{dataType === 'rca' ? '🌩️' : '👤'}</span>
                                            <span className="slack-sender">{selectedProblem.requester}</span>
                                            <span className="slack-time">오늘 오전 10:30</span>
                                            {dataType === 'rca' && <span className="anomaly-badge">ABNORMALITY DETECTED</span>}
                                        </div>
                                        <div className="slack-content">
                                            {renderMarkdown(selectedProblem.question)}
                                        </div>
                                        {selectedProblem.context && (
                                            <div className="slack-context">
                                                ℹ️ {renderMarkdown(selectedProblem.context)}
                                            </div>
                                        )}
                                    </div>
                                )}

                                {selectedProblem.expected_columns && (
                                    <div className="section">
                                        <div className="section-title">결과 컬럼</div>
                                        <div className="columns-box">
                                            {selectedProblem.expected_columns.map((col, i) => (
                                                <code key={i}>{col}</code>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {selectedProblem.hint && (
                                    <details className="hint-section">
                                        <summary>💬 힌트 보기</summary>
                                        <p>{selectedProblem.hint}</p>
                                    </details>
                                )}
                            </div>
                        )}

                        {problems.length === 0 && (
                            <div className="no-problems">
                                {isFetching ? (
                                    <div className="fetching-state-container">
                                        <div className="fetching-status-badge">
                                            <span className="pulse-dot"></span>
                                            오늘의 문제 찾는 중...
                                        </div>
                                        <div className="fetching-state">
                                            {/* <p>오늘의 {dataType.toUpperCase()} 문제를 찾는 중입니다...잠시만 기다려주세요</p> */}
                                            <div className="loading-spinner" />
                                        </div>
                                    </div>
                                ) : (
                                    <div className="empty-state">
                                        <p>오늘 {dataType.toUpperCase()} 문제가 없습니다.</p>
                                        <button
                                            onClick={loadData}
                                            className="btn-refresh"
                                            style={{
                                                marginTop: '1.5rem',
                                                padding: '0.6rem 1.2rem',
                                                background: 'var(--accent-color)',
                                                color: 'white',
                                                border: 'none',
                                                borderRadius: '6px',
                                                cursor: 'pointer',
                                                fontWeight: 600
                                            }}
                                        >
                                            🔄 다시 검색하기
                                        </button>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                ) : (
                    <TableSchema tables={tables} />
                )}
            </div>

            <div className="resizer" ref={resizerRef} onMouseDown={handleMouseDown} />

            {/* 우측 패널 */}
            <div className="right-panel" ref={rightPanelRef} style={{ width: `${100 - leftWidth}%` }}>
                <div className="editor-section" style={{ height: `${editorHeightPercent}%` }}>
                    <div className="editor-header">
                        <span>SQL 에디터 <small style={{ marginLeft: '10px', color: 'var(--text-secondary)', fontWeight: 'normal' }}>(PostgreSQL 전용)</small></span>
                        {track === 'future' && (
                            <div className="translate-bar">
                                <input
                                    type="text"
                                    placeholder="자연어로 질문하여 SQL 생성 (예: 매출 상위 5명...)"
                                    value={translateQuery}
                                    onChange={(e) => setTranslateQuery(e.target.value)}
                                    onKeyDown={(e) => e.key === 'Enter' && handleTranslate()}
                                />
                                <button onClick={handleTranslate} disabled={translating || !translateQuery.trim()}>
                                    {translating ? '⏳' : '🤖'}<span className="badge-new-tiny" style={{ background: '#6366f1' }}>AI</span>
                                </button>
                            </div>
                        )}
                        <span className="shortcut">Ctrl+Enter로 실행</span>
                    </div>
                    <div className="editor-shell">
                        <SQLEditor
                            value={sql}
                            onChange={(val) => {
                                setSql(val);
                                if (selectedProblem && val.trim().length > 0 && lastAttemptedRef.current !== selectedProblem.problem_id) {
                                    analytics.problemAttempted(selectedProblem.problem_id, selectedProblem.difficulty);
                                    lastAttemptedRef.current = selectedProblem.problem_id;
                                }
                            }}
                            onExecute={handleExecute}
                            height="calc(100% - 80px)" // header + actions
                            tables={tables}
                        />
                    </div>
                    <div className="editor-actions">
                        <button onClick={handleExecute} disabled={loading} className="btn-execute">
                            {loading ? '실행 중...' : '실행'}
                        </button>
                        <div className="spacer" />
                        {/* AI 도움 버튼 (문제당 1회) */}
                        <div className="ai-help-container" style={{ position: 'relative' }}>
                            <button 
                                onClick={() => setShowAiHelpMenu(!showAiHelpMenu)}
                                disabled={aiHelpLoading || !selectedProblem || (selectedProblem && aiHelpUsed[selectedProblem.problem_id])}
                                className="btn-ai-help"
                                title={selectedProblem && aiHelpUsed[selectedProblem.problem_id] ? '이미 사용됨' : 'AI 도움 받기'}
                            >
                                {aiHelpLoading ? '⏳' : '🤖'} AI 도움
                                {selectedProblem && !aiHelpUsed[selectedProblem.problem_id] && (
                                    <span className="badge-count">1</span>
                                )}
                            </button>
                            {showAiHelpMenu && selectedProblem && !aiHelpUsed[selectedProblem.problem_id] && (
                                <div className="ai-help-menu">
                                    <button onClick={() => handleAiHelp('hint')}>
                                        💡 힌트 받기
                                    </button>
                                    <button onClick={() => handleAiHelp('solution')}>
                                        📝 쿼리 작성해줘
                                    </button>
                                </div>
                            )}
                        </div>
                        <button onClick={handleSubmit} disabled={submitting || !selectedProblem} className="btn-submit">
                            {submitting ? '채점 중...' : '제출'}
                        </button>
                    </div>
                </div>

                <div className="v-resizer" onMouseDown={handleMouseDownVertical} />

                <ResultPanel
                    result={result}
                    submitResult={submitResult}
                    aiHelpResult={aiHelpResult}
                    insightLoading={insightLoading}
                    aiHelpLoading={aiHelpLoading}
                    submitting={submitting}
                    showInsightModal={showInsightModal}
                    setShowInsightModal={setShowInsightModal}
                    selectedProblem={selectedProblem}
                    track={track}
                    handleInsight={handleInsight}
                    tables={tables}
                    insightData={insightData}
                    onQuerySelect={(newSql) => {
                        setSql(newSql);
                        setResult(null);
                        setSubmitResult(null);

                        analytics.aiSuggestionApplied('query', {
                            problemId: selectedProblem?.problem_id,
                            dataType: dataType
                        });
                    }}
                />
            </div>

            {/* AI 인사이트 모달 */}
            <InsightModal
                isOpen={showInsightModal}
                onClose={() => setShowInsightModal(false)}
                insightData={insightData}
                onQuerySelect={(newSql) => {
                    setSql(newSql);
                    setResult(null);
                    setSubmitResult(null);

                    analytics.aiSuggestionApplied('query', {
                        problemId: selectedProblem?.problem_id,
                        dataType: dataType
                    });
                }}
            />
        </div>
    );
}
