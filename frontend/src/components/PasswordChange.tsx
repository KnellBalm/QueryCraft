import { useState } from 'react';
import { authApi } from '../api/client';

interface PasswordChangeProps {
    onSuccess: (message: string) => void;
    onError: (message: string) => void;
}

export function PasswordChange({ onSuccess, onError }: PasswordChangeProps) {
    const [currentPassword, setCurrentPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        
        if (newPassword !== confirmPassword) {
            onError('새 비밀번호가 일치하지 않습니다.');
            return;
        }

        if (newPassword.length < 8) {
            onError('비밀번호는 8자 이상이어야 합니다.');
            return;
        }

        setLoading(true);
        try {
            const res = await authApi.changePassword(currentPassword, newPassword);
            if (res.data.success) {
                onSuccess('비밀번호가 성공적으로 변경되었습니다 ✓');
                setCurrentPassword('');
                setNewPassword('');
                setConfirmPassword('');
            }
        } catch (err: any) {
            onError(err.response?.data?.detail || '비밀번호 변경에 실패했습니다.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <form className="password-change-form" onSubmit={handleSubmit}>
            <div className="form-group">
                <label>현재 비밀번호</label>
                <input
                    type="password"
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                    placeholder="현재 비밀번호를 입력하세요"
                    required
                />
            </div>
            <div className="form-group">
                <label>새 비밀번호</label>
                <input
                    type="password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="새 비밀번호 (8자 이상, 대소문자/숫자/특수문자)"
                    required
                />
            </div>
            <div className="form-group">
                <label>새 비밀번호 확인</label>
                <input
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="새 비밀번호를 한 번 더 입력하세요"
                    required
                />
            </div>
            <button type="submit" className="btn-change-password" disabled={loading}>
                {loading ? '변경 중...' : '비밀번호 변경'}
            </button>
        </form>
    );
}
