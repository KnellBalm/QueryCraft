import { Card, Badge } from '../ui';
import { Skeleton } from '../Skeleton';

interface AdminOverviewProps {
    status: any;
    today: string;
}

export function AdminOverview({ status, today }: AdminOverviewProps) {
    return (
        <Card className="admin-overview-card">
            <div className="admin-overview-header">
                <h2 style={{ margin: 0 }}>🌟 시스템 현황 요약 ({today})</h2>
            </div>

            <div className="status-grid" style={{ marginTop: '1.5rem', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem' }}>
                {/* 시스템 연결 상태 */}
                <section className="status-group">
                    <h3 style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>인프라 연결</h3>
                    {status ? (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                            <div className="status-item-compact" style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0.75rem', background: 'var(--bg-tertiary)', borderRadius: '6px' }}>
                                <span>PostgreSQL</span>
                                <span style={{ color: status.postgres_connected ? 'var(--success-color)' : 'var(--error-color)', fontWeight: 600 }}>
                                    {status.postgres_connected ? '● Connected' : '○ Disconnected'}
                                </span>
                            </div>
                            <div className="status-item-compact" style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0.75rem', background: 'var(--bg-tertiary)', borderRadius: '6px' }}>
                                <span>DuckDB</span>
                                <span style={{ color: status.duckdb_connected ? 'var(--success-color)' : 'var(--error-color)', fontWeight: 600 }}>
                                    {status.duckdb_connected ? '● Connected' : '○ Disconnected'}
                                </span>
                            </div>
                        </div>
                    ) : (
                        <Skeleton variant="card" height="80px" />
                    )}
                </section>

                {/* 오늘의 문제 상태 */}
                <section className="status-group">
                    <h3 style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>오늘의 콘텐츠</h3>
                    {status?.today_problems ? (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                            <div className="status-item-compact" style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0.75rem', background: 'var(--bg-tertiary)', borderRadius: '6px' }}>
                                <span>생성 여부</span>
                                <span style={{ color: status.today_problems.exists ? 'var(--success-color)' : 'var(--error-color)', fontWeight: 600 }}>
                                    {status.today_problems.exists ? `Ready (${status.today_problems.count})` : 'Missing'}
                                </span>
                            </div>
                            {status.today_problems.difficulties && (
                                <div style={{ display: 'flex', gap: '0.25rem', marginTop: '0.25rem' }}>
                                    {Object.entries(status.today_problems.difficulties).map(([diff, cnt]) => (
                                        <Badge key={diff} variant={diff === 'hard' ? 'error' : diff === 'medium' ? 'warning' : 'success'}>
                                            {diff}: {cnt as number}
                                        </Badge>
                                    ))}
                                </div>
                            )}
                        </div>
                    ) : (
                        <div style={{ padding: '0.75rem', background: 'rgba(239, 68, 68, 0.1)', borderRadius: '8px', border: '1px solid rgba(239, 68, 68, 0.2)', color: 'var(--error-color)', fontSize: '0.85rem' }}>
                            ⚠️ 문제 파일이 생성되지 않았습니다. 통합 생성을 실행해주세요.
                        </div>
                    )}
                </section>
            </div>
        </Card>
    );
}
