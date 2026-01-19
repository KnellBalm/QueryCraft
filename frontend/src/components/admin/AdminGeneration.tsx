import { useState } from 'react';
import { Card, Button, Badge } from '../ui';
import { adminApi } from '../../api/client';

interface AdminGenerationProps {
    problemFiles: any[];
    onRefresh: () => void;
    onShowMessage: (msg: string) => void;
}

export function AdminGeneration({ problemFiles, onRefresh, onShowMessage }: AdminGenerationProps) {
    const [loading, setLoading] = useState(false);

    const handleTriggerNow = async () => {
        setLoading(true);
        try {
            const res = await adminApi.triggerNow();
            onShowMessage(res.data.message || '통합 생성 완료');
            onRefresh();
        } catch (e) {
            onShowMessage('통합 생성 실패');
        } finally {
            setLoading(false);
        }
    };

    const handleRcaTrigger = async () => {
        setLoading(true);
        try {
            const res = await adminApi.generateProblems('rca');
            onShowMessage(res.data.message || 'RCA 문제 생성 완료');
            onRefresh();
        } catch (e) {
            onShowMessage('RCA 생성 오답');
        } finally {
            setLoading(false);
        }
    };

    const handleReset = async () => {
        if (window.confirm('⚠️ 모든 제출 기록이 초기화되며 복구할 수 없습니다. 계속하시겠습니까?')) {
            setLoading(true);
            try {
                await adminApi.resetSubmissions();
                localStorage.removeItem('completed_pa');
                localStorage.removeItem('completed_stream');
                onShowMessage('전체 기록 초기화 완료');
                setTimeout(() => window.location.reload(), 1000);
            } catch (e) {
                onShowMessage('초기화 실패');
            } finally {
                setLoading(false);
            }
        }
    };

    return (
        <div className="admin-generation-flow">
            {/* 액션 카드 */}
            <Card className="generation-action-card" style={{ marginBottom: '2rem', border: '1px solid var(--accent-color)', background: 'rgba(99, 102, 241, 0.05)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                    <div>
                        <h2 style={{ margin: 0 }}>🚀 통합 세대 관리</h2>
                        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '0.4rem' }}>
                            산업군 선정부터 데이터 적재, AI 문제 출제까지 한 번에 실행합니다.
                        </p>
                    </div>
                    <Badge variant="success">Engine v2.0</Badge>
                </div>

                <div className="action-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                    <Button
                        onClick={handleTriggerNow}
                        loading={loading}
                        size="lg"
                        className="full-gen-btn"
                        style={{ height: '80px', fontSize: '1.1rem', fontWeight: 700 }}
                    >
                        오늘의 통합 생성 실행 (Data + SQL)
                    </Button>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                        <Button variant="secondary" onClick={handleRcaTrigger} loading={loading}>
                            🔍 RCA 시나리오 수동 트리거
                        </Button>
                        <Button variant="secondary" onClick={onRefresh} disabled={loading}>
                            🔃 시스템 상태 동기화
                        </Button>
                    </div>
                </div>

                <div style={{ marginTop: '1.5rem', paddingTop: '1.5rem', borderTop: '1px solid var(--border-color)', display: 'flex', justifyContent: 'flex-end' }}>
                    <Button variant="danger" size="sm" onClick={handleReset} loading={loading}>
                        🗑️ 전체 학습 기록 초기화
                    </Button>
                </div>
            </Card>

            {/* 파일 목록 카드 */}
            <Card>
                <h3 style={{ marginTop: 0, marginBottom: '1.2rem' }}>📝 생성된 문제 파일 상세</h3>
                {problemFiles.length > 0 ? (
                    <div className="admin-table-container" style={{ overflowX: 'auto' }}>
                        <table className="admin-table" style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
                            <thead>
                                <tr style={{ textAlign: 'left', borderBottom: '2px solid var(--bg-tertiary)' }}>
                                    <th style={{ padding: '0.75rem' }}>타입</th>
                                    <th style={{ padding: '0.75rem' }}>파일명</th>
                                    <th style={{ padding: '0.75rem' }}>문제 수</th>
                                    <th style={{ padding: '0.75rem' }}>생성 일시</th>
                                </tr>
                            </thead>
                            <tbody>
                                {problemFiles.map((f, i) => (
                                    <tr key={i} style={{ borderBottom: '1px solid var(--bg-tertiary)' }}>
                                        <td style={{ padding: '0.75rem' }}>
                                            <Badge variant={f.type === 'pa' ? 'default' : 'info'}>{f.type.toUpperCase()}</Badge>
                                        </td>
                                        <td style={{ padding: '0.75rem', fontFamily: 'monospace' }}>{f.filename}</td>
                                        <td style={{ padding: '0.75rem' }}>{f.problem_count}개</td>
                                        <td style={{ padding: '0.75rem', color: 'var(--text-muted)' }}>{new Date(f.created_at).toLocaleString()}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                ) : (
                    <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
                        생성된 파일 이력이 없습니다.
                    </div>
                )}
            </Card>
        </div>
    );
}
