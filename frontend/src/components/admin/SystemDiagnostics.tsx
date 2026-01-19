import { useEffect, useState } from 'react';
import { Card, Badge } from '../ui';
import { adminApi } from '../../api/client';

export function SystemDiagnostics() {
    const [apiUsage, setApiUsage] = useState<any>(null);
    const [logs, setLogs] = useState<any[]>([]);
    const [logCategory, setLogCategory] = useState('');

    const loadDiagnostics = async () => {
        try {
            const [usageRes, logsRes] = await Promise.all([
                adminApi.getApiUsage(7, 50),
                adminApi.getLogs(logCategory || undefined, undefined, 50)
            ]);
            setApiUsage(usageRes.data);
            setLogs(logsRes.data.logs || []);
        } catch (e) {
            console.error(e);
        }
    };

    useEffect(() => {
        loadDiagnostics();
    }, [logCategory]);

    return (
        <div className="system-diagnostics">
            {/* API 사용량 */}
            <Card style={{ marginBottom: '2rem' }}>
                <h2 style={{ margin: '0 0 1.5rem 0' }}>💰 AI API Usage (Gemini)</h2>
                {apiUsage ? (
                    <div className="usage-stats" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem' }}>
                        <div style={{ padding: '1rem', background: 'var(--bg-tertiary)', borderRadius: '8px' }}>
                            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Estimated Cost (7d)</div>
                            <div style={{ fontSize: '1.5rem', fontWeight: 700, color: '#f59e0b' }}>${apiUsage.summary?.estimated_cost_usd || 0}</div>
                        </div>
                        <div style={{ padding: '1rem', background: 'var(--bg-tertiary)', borderRadius: '8px' }}>
                            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Total Tokens</div>
                            <div style={{ fontSize: '1.5rem', fontWeight: 700 }}>{(apiUsage.summary?.total_tokens || 0).toLocaleString()}</div>
                        </div>
                        <div style={{ padding: '1rem', background: 'var(--bg-tertiary)', borderRadius: '8px' }}>
                            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Total Calls</div>
                            <div style={{ fontSize: '1.5rem', fontWeight: 700 }}>{apiUsage.summary?.total_calls || 0}회</div>
                        </div>
                    </div>
                ) : <p>Loading usage data...</p>}
            </Card>

            {/* 시스템 로그 */}
            <Card>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                    <h2 style={{ margin: 0 }}>📋 System Logs</h2>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                        {['', 'problem_generation', 'scheduler', 'system', 'api'].map(cat => (
                            <button
                                key={cat}
                                onClick={() => setLogCategory(cat)}
                                style={{
                                    padding: '4px 10px',
                                    borderRadius: '6px',
                                    border: '1px solid var(--border-color)',
                                    background: logCategory === cat ? 'var(--accent-color)' : 'var(--bg-tertiary)',
                                    color: logCategory === cat ? 'white' : 'var(--text-primary)',
                                    fontSize: '0.75rem',
                                    cursor: 'pointer'
                                }}
                            >
                                {cat || 'All'}
                            </button>
                        ))}
                    </div>
                </div>

                <div style={{ maxHeight: '400px', overflowY: 'auto', background: 'var(--bg-primary)', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
                        <thead style={{ position: 'sticky', top: 0, background: 'var(--bg-tertiary)', zIndex: 1 }}>
                            <tr style={{ textAlign: 'left' }}>
                                <th style={{ padding: '0.75rem' }}>Timestamp</th>
                                <th style={{ padding: '0.75rem' }}>Level</th>
                                <th style={{ padding: '0.75rem' }}>Message</th>
                            </tr>
                        </thead>
                        <tbody>
                            {logs.map((log, i) => (
                                <tr key={i} style={{ borderBottom: '1px solid var(--bg-tertiary)' }}>
                                    <td style={{ padding: '0.6rem 0.75rem', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                                        {new Date(log.created_at).toLocaleString()}
                                    </td>
                                    <td style={{ padding: '0.6rem 0.75rem' }}>
                                        <Badge variant={log.level === 'error' ? 'error' : log.level === 'warning' ? 'warning' : 'info'}>
                                            {log.level.toUpperCase()}
                                        </Badge>
                                    </td>
                                    <td style={{ padding: '0.6rem 0.75rem' }}>{log.message}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                    {logs.length === 0 && <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>No logs found.</div>}
                </div>
            </Card>
        </div>
    );
}
