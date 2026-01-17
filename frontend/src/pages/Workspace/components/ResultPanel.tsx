// frontend/src/pages/Workspace/components/ResultPanel.tsx
import React from 'react';
import { ResultTable } from '../../../components/ResultTable';
import type { SQLExecuteResponse, SubmitResponse, Problem, TableSchema as Schema } from '../../../types';

// Simple markdown renderer (bold, code, line breaks)
function renderMarkdown(text: string | undefined | null) {
    if (!text) return null;
    const html = text
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')  // **bold**
        .replace(/`(.+?)`/g, '<code>$1</code>')            // `code`
        .replace(/\n/g, '<br/>');                          // line breaks
    return <span dangerouslySetInnerHTML={{ __html: html }} />;
}

interface ResultPanelProps {
    result: SQLExecuteResponse | null;
    submitResult: SubmitResponse | null;
    aiHelpResult: { type: string; content: string } | null;
    insightLoading: boolean;
    aiHelpLoading: boolean;
    submitting: boolean;
    showInsightModal: boolean;
    setShowInsightModal: (show: boolean) => void;
    selectedProblem: Problem | undefined;
    track: 'core' | 'future';
    handleInsight: () => void;
    tables: Schema[];
    insightData: any;
    onQuerySelect?: (sql: string) => void;
}

export const ResultPanel = React.memo<ResultPanelProps>(({
    result,
    submitResult,
    aiHelpResult,
    insightLoading,
    aiHelpLoading,
    submitting,
    track,
    handleInsight,
}) => {
    return (
        <div className="result-section">
            <div className="result-header">
                <span>실행 결과</span>
                <div className="result-meta">
                    {/* Future Lab에서만 AI 인사이트 표시 */}
                    {track === 'future' && result?.success && result.data && result.data.length > 0 && (
                        <button className="btn-insight-trigger" onClick={handleInsight} disabled={insightLoading}>
                            {insightLoading ? '⚡ 분석 중...' : '✨ AI 인사이트'}<span className="badge-new-tiny">NEW</span>
                        </button>
                    )}
                    {result?.execution_time_ms && (
                        <span className="exec-time">{result.execution_time_ms.toFixed(0)}ms</span>
                    )}
                </div>
            </div>

            <div className="result-content">
                {/* 로딩 상태 */}
                {(submitting || aiHelpLoading) && (
                    <div className="loading-state">
                        <div className="loading-spinner" />
                        <div className="loading-text">
                            {submitting ? '채점 중입니다...' : 'AI가 도움을 준비 중입니다...'}
                        </div>
                    </div>
                )}

                {/* AI 도움 결과 */}
                {aiHelpResult && !aiHelpLoading && (
                    <div className={`ai-help-result ${aiHelpResult.type}`}>
                        <div className="ai-help-header">
                            {aiHelpResult.type === 'hint' ? '💡 AI 힌트' :
                             aiHelpResult.type === 'solution' ? '📝 AI 솔루션' : '⚠️ 오류'}
                        </div>
                        <div className="ai-help-content">
                            {renderMarkdown(aiHelpResult.content)}
                        </div>
                    </div>
                )}

                {/* 제출 결과 */}
                {submitResult && !submitting && (
                    <div className={`submit-result ${submitResult.is_correct ? 'correct' : 'wrong'}`}>
                        <div className="result-icon">
                            {submitResult.is_correct ? '정답입니다!' : '오답입니다'}
                        </div>
                        <div className="feedback">{submitResult.feedback}</div>
                    </div>
                )}

                {/* 쿼리 결과 */}
                {result && result.success && result.data && !submitting && !aiHelpLoading && (
                    <ResultTable columns={result.columns || []} data={result.data} />
                )}

                {result && !result.success && !submitting && !aiHelpLoading && (
                    <div className="error-result">오류: {result.error}</div>
                )}

                {!result && !submitResult && !aiHelpResult && !submitting && !aiHelpLoading && (
                    <div className="empty-result">SQL을 작성하고 실행 버튼을 누르세요</div>
                )}
            </div>
        </div>
    );
});

ResultPanel.displayName = 'ResultPanel';
