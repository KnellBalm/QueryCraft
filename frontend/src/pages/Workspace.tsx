// frontend/src/pages/Workspace.tsx
import { useEffect, useState, useCallback, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { SQLEditor } from '../components/SQLEditor';
import { TableSchema } from '../components/TableSchema';
import { InsightModal } from '../components/InsightModal';
import { ResultPanel } from './Workspace/components/ResultPanel';
import { ProblemListPanel } from './Workspace/components/ProblemListPanel';
import { useTrack } from '../contexts/TrackContext';
import { useProblemCompletion } from '../hooks/useProblemCompletion';
import { problemsApi, sqlApi } from '../api/client';
import { analytics } from '../services/analytics';
import type { Problem, TableSchema as Schema, SQLExecuteResponse, SubmitResponse } from '../types';
import './Workspace.css';

interface WorkspaceProps {
    dataType?: 'pa' | 'stream' | 'rca';
}

export function Workspace({ dataType: propDataType }: WorkspaceProps) {
    const { dataType: paramDataType } = useParams<{ dataType: any }>();
    const dataType = (propDataType || paramDataType || 'pa') as 'pa' | 'stream' | 'rca';

    const [problems, setProblems] = useState<Problem[]>([]);
    const [isFetching, setIsFetching] = useState(false);
    const [selectedIndex, setSelectedIndex] = useState(0);
    const [tables, setTables] = useState<Schema[]>([]);
    const [sql, setSql] = useState('');
    const [result, setResult] = useState<SQLExecuteResponse | null>(null);
    const [submitResult, setSubmitResult] = useState<SubmitResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [submitting, setSubmitting] = useState(false);
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
    const [aiHelpUsed, setAiHelpUsed] = useState<{ [problemId: string]: boolean }>({});
    const [aiHelpResult, setAiHelpResult] = useState<{ type: string; content: string } | null>(null);
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
        const pagePath = dataType === 'pa' ? '/pa-practice' :
            dataType === 'stream' ? '/stream-practice' : '/rca-practice';
        analytics.pageView(pagePath, { data_type: dataType });
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
        setAiHelpResult(null); // Clear previous AI help/error

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
        setAiHelpResult(null); // Clear previous AI help/error
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

    // 문제 선택 핸들러
    const handleSelectProblem = useCallback((index: number) => {
        setSelectedIndex(index);
        setSql('');
        setSubmitResult(null);
        setResult(null);
    }, []);

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
                    <ProblemListPanel
                        problems={problems}
                        selectedIndex={selectedIndex}
                        metadata={metadata}
                        isFetching={isFetching}
                        dataType={dataType}
                        onSelectProblem={handleSelectProblem}
                        onRefresh={loadData}
                        getStatusIcon={getStatusIcon}
                    />
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
                            height="calc(100%)" // header + actions  #에디터 작동 안하면 100% - 80px 로 변경
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
                    dataType={dataType}
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
