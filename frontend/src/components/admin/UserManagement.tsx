import { useEffect, useState } from 'react';
import { Card, Button, Badge } from '../ui';
import { adminApi } from '../../api/client';

export function UserManagement() {
    const [users, setUsers] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);

    const loadUsers = async () => {
        setLoading(true);
        try {
            const res = await adminApi.getUsers();
            setUsers(res.data.users || []);
        } catch (e) {
            setUsers([]);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadUsers();
    }, []);

    const handleToggleAdmin = async (userId: string) => {
        try {
            await adminApi.toggleAdmin(userId);
            loadUsers();
        } catch (e) {
            alert('권한 변경에 실패했습니다.');
        }
    };

    const handleDeleteUser = async (userId: string, email: string) => {
        if (window.confirm(`정말 ${email} 사용자를 삭제하시겠습니까?`)) {
            try {
                await adminApi.deleteUser(userId);
                loadUsers();
            } catch (e) {
                alert('삭제에 실패했습니다.');
            }
        }
    };

    return (
        <Card className="user-management-card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                <h2 style={{ margin: 0 }}>👥 사용자 및 권한 관리</h2>
                <Button variant="secondary" size="sm" onClick={loadUsers} loading={loading}>
                    🔄 목록 새로고침
                </Button>
            </div>

            <div className="admin-table-container" style={{ overflowX: 'auto' }}>
                <table className="admin-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead>
                        <tr style={{ textAlign: 'left', borderBottom: '2px solid var(--bg-tertiary)', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                            <th style={{ padding: '1rem' }}>사용자 정보</th>
                            <th style={{ padding: '1rem' }}>경험치 / 레벨</th>
                            <th style={{ padding: '1rem' }}>권한</th>
                            <th style={{ padding: '1rem' }}>가입일</th>
                            <th style={{ padding: '1rem' }}>액션</th>
                        </tr>
                    </thead>
                    <tbody>
                        {users.map((u) => (
                            <tr key={u.id} style={{ borderBottom: '1px solid var(--bg-tertiary)' }}>
                                <td style={{ padding: '1rem' }}>
                                    <div style={{ fontWeight: 600 }}>{u.nickname || u.name || 'Unknown'}</div>
                                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{u.email}</div>
                                </td>
                                <td style={{ padding: '1rem' }}>
                                    <Badge variant="default">Lv.{u.level}</Badge>
                                    <span style={{ marginLeft: '0.5rem', fontSize: '0.85rem' }}>{u.xp} XP</span>
                                </td>
                                <td style={{ padding: '1rem' }}>
                                    <button
                                        onClick={() => handleToggleAdmin(u.id)}
                                        style={{
                                            padding: '4px 12px',
                                            borderRadius: '20px',
                                            border: 'none',
                                            fontSize: '0.75rem',
                                            fontWeight: 600,
                                            cursor: 'pointer',
                                            background: u.is_admin ? 'var(--success-color)' : 'var(--bg-tertiary)',
                                            color: u.is_admin ? '#fff' : 'var(--text-secondary)'
                                        }}
                                    >
                                        {u.is_admin ? 'Admin' : 'User'}
                                    </button>
                                </td>
                                <td style={{ padding: '1rem', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                                    {u.created_at ? new Date(u.created_at).toLocaleDateString() : '-'}
                                </td>
                                <td style={{ padding: '1rem' }}>
                                    <Button variant="danger" size="sm" onClick={() => handleDeleteUser(u.id, u.email)}>
                                        삭제
                                    </Button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </Card>
    );
}
