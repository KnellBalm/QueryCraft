// frontend/src/pages/Workspace/components/ProblemListPanel.tsx
import React from 'react';
import type { Problem, DatasetMetadata } from '../../../types';

// 간단한 마크다운 변환 (볼드, 코드, 줄바꿈)
function renderMarkdown(text: string | undefined | null) {
    if (!text) return null;
    const html = text
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')  // **bold**
        .replace(/`(.+?)`/g, '<code>$1</code>')            // `code`
        .replace(/\n/g, '<br/>');                          // 줄바꿈
    return <span dangerouslySetInnerHTML={{ __html: html }} />;
}

interface ProblemListPanelProps {
    problems: Problem[];
    selectedIndex: number;
    metadata: DatasetMetadata | null;
    scenario?: any; // 추가
    isFetching: boolean;
    dataType: 'pa' | 'stream' | 'rca';
    onSelectProblem: (index: number) => void;
    onRefresh: () => void;
    getStatusIcon: (problemId: string) => string;
}

export const ProblemListPanel = React.memo(function ProblemListPanel({
    problems,
    selectedIndex,
    metadata,
    scenario, // 추가
    isFetching,
    dataType,
    onSelectProblem,
    onRefresh,
    getStatusIcon,
}: ProblemListPanelProps) {
    const selectedProblem = problems[selectedIndex] || null;

    const difficultyIcon: Record<string, string> = {
        easy: '🟢', medium: '🟡', hard: '🔴',
    };

    return (
        <div className="problem-panel">
            <div className="problem-list">
                {Array.isArray(problems) && problems.map((p, idx) => (
                    <button
                        key={p.problem_id}
                        className={`problem-item ${selectedIndex === idx ? 'active' : ''}`}
                        onClick={() => onSelectProblem(idx)}
                    >
                        <span className="status">{getStatusIcon(p.problem_id)}</span>
                        <span className="num">{idx + 1}번</span>
                        <span className="difficulty">{difficultyIcon[p.difficulty]}</span>
                    </button>
                ))}
            </div>



            {scenario && (
                <div className="daily-scenario-context">
                    <div className="scenario-title-bar">
                        <span className="scenario-label">📅 오늘의 상황</span>
                        <span className="scenario-date">{scenario.date}</span>
                    </div>
                    <div className="scenario-description">
                        {renderMarkdown(scenario.background || scenario.story)}
                    </div>
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
                            {metadata && (
                                <div className="dataset-context simplified">
                                    <div className="context-header">
                                        <span className={`company-badge ${dataType === 'rca' ? 'rca' : ''}`}>
                                            {dataType === 'rca' ? '🚨 ANOMALY' : 'CONTEXT'}
                                        </span>
                                        <span className="company-name-tiny">{metadata.company_name}</span>
                                        <span className="product-type-tag">{metadata.product_type}</span>
                                    </div>
                                    {metadata.north_star && (
                                        <div className="kpi-mini">
                                            <span className="kpi-label">Goal:</span>
                                            <span className="kpi-value">✨ {metadata.north_star}</span>
                                        </div>
                                    )}
                                </div>
                            )}

                            <div className="slack-header">
                                <span className="slack-avatar">{dataType === 'rca' ? '🌩️' : '👤'}</span>
                                <span className="slack-sender">{selectedProblem.requester}</span>
                                <span className="slack-time">{new Date().toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit', hour12: true })}</span>
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
                            <summary>💬 분석 힌트</summary>
                            <div className="hint-content">
                                <p>{selectedProblem.hint}</p>
                                {selectedProblem.hints && selectedProblem.hints.length > 0 && (
                                    <div className="sequential-hints">
                                        <div className="seq-hint-title">단계별 가이드</div>
                                        {selectedProblem.hints.map((h, i) => (
                                            <details key={i} className="seq-hint-item">
                                                <summary>Step {i + 1} 가이드</summary>
                                                <div className="seq-hint-body">
                                                    {renderMarkdown(h)}
                                                </div>
                                            </details>
                                        ))}
                                    </div>
                                )}
                            </div>
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
                                <div className="loading-spinner" />
                            </div>
                        </div>
                    ) : (
                        <div className="empty-state">
                            <p>오늘 {dataType.toUpperCase()} 문제가 없습니다.</p>
                            <button
                                onClick={onRefresh}
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
    );
});
