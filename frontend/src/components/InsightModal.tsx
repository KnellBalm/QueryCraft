// frontend/src/components/InsightModal.tsx
import { useState } from 'react';
import './InsightModal.css';

interface SuggestedQuery {
    title: string;
    sql: string;
}

interface InsightData {
    key_findings: string[];
    insights: string[];
    action_items: string[];
    suggested_queries: SuggestedQuery[];
    report_markdown: string;
}

interface InsightModalProps {
    isOpen: boolean;
    onClose: () => void;
    insightData: InsightData | null;
    onQuerySelect?: (sql: string) => void;
}

export function InsightModal({ isOpen, onClose, insightData, onQuerySelect }: InsightModalProps) {
    const [copiedSection, setCopiedSection] = useState<string | null>(null);

    if (!isOpen || !insightData) return null;

    const copyToClipboard = (text: string, section: string) => {
        navigator.clipboard.writeText(text);
        setCopiedSection(section);
        setTimeout(() => setCopiedSection(null), 2000);
    };

    const downloadMarkdown = () => {
        const blob = new Blob([insightData.report_markdown], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `ai-insight-${new Date().toISOString().split('T')[0]}.md`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    };

    return (
        <div className="insight-modal-overlay" onClick={onClose}>
            <div className="insight-modal" onClick={(e) => e.stopPropagation()}>
                <div className="insight-modal-header">
                    <h2>🤖 AI 인사이트 리포트</h2>
                    <button className="close-btn" onClick={onClose}>✕</button>
                </div>

                <div className="insight-modal-content">
                    {/* 핵심 발견 */}
                    <section className="insight-section">
                        <div className="insight-section-header">
                            <h3>📌 핵심 발견 (Key Findings)</h3>
                            <button
                                className="copy-btn"
                                onClick={() => copyToClipboard(insightData.key_findings.join('\n'), 'findings')}
                            >
                                {copiedSection === 'findings' ? '✓ 복사됨' : '📋 복사'}
                            </button>
                        </div>
                        <ol className="finding-list">
                            {insightData.key_findings.map((finding, idx) => (
                                <li key={idx}>{finding}</li>
                            ))}
                        </ol>
                    </section>

                    {/* 비즈니스 인사이트 */}
                    {insightData.insights.length > 0 && (
                        <section className="insight-section">
                            <div className="insight-section-header">
                                <h3>💡 비즈니스 인사이트</h3>
                                <button
                                    className="copy-btn"
                                    onClick={() => copyToClipboard(insightData.insights.join('\n'), 'insights')}
                                >
                                    {copiedSection === 'insights' ? '✓ 복사됨' : '📋 복사'}
                                </button>
                            </div>
                            <ul className="insight-list">
                                {insightData.insights.map((insight, idx) => (
                                    <li key={idx}>{insight}</li>
                                ))}
                            </ul>
                        </section>
                    )}

                    {/* 추천 액션 */}
                    {insightData.action_items.length > 0 && (
                        <section className="insight-section">
                            <div className="insight-section-header">
                                <h3>🎯 추천 액션 (Action Items)</h3>
                                <button
                                    className="copy-btn"
                                    onClick={() => copyToClipboard(insightData.action_items.join('\n'), 'actions')}
                                >
                                    {copiedSection === 'actions' ? '✓ 복사됨' : '📋 복사'}
                                </button>
                            </div>
                            <ol className="action-list">
                                {insightData.action_items.map((action, idx) => (
                                    <li key={idx}>{action}</li>
                                ))}
                            </ol>
                        </section>
                    )}

                    {/* 추가 분석 제안 */}
                    {insightData.suggested_queries.length > 0 && (
                        <section className="insight-section">
                            <h3>🔍 추가 분석 제안</h3>
                            <div className="suggested-queries">
                                {insightData.suggested_queries.map((query, idx) => (
                                    <div key={idx} className="suggested-query">
                                        <h4>{query.title}</h4>
                                        <pre className="query-code">{query.sql}</pre>
                                        {onQuerySelect && (
                                            <button
                                                className="use-query-btn"
                                                onClick={() => {
                                                    onQuerySelect(query.sql);
                                                    onClose();
                                                }}
                                            >
                                                ▶ 쿼리 실행
                                            </button>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </section>
                    )}
                </div>

                <div className="insight-modal-footer">
                    <button className="download-btn" onClick={downloadMarkdown}>
                        ⬇ 마크다운 다운로드
                    </button>
                    <button className="close-footer-btn" onClick={onClose}>
                        닫기
                    </button>
                </div>
            </div>
        </div>
    );
}
