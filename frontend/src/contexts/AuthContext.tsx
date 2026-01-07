// frontend/src/contexts/AuthContext.tsx
import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import { api } from '../api/client';

interface User {
    id: string;
    email: string;
    name: string;
    nickname?: string;
    is_admin?: boolean;
    xp?: number;
    level?: number;
    created_at?: string;
}

import { analytics } from '../services/analytics';

interface AuthContextType {
    user: User | null;
    isLoading: boolean;
    login: (email: string, password: string) => Promise<{ success: boolean; error?: string }>;
    register: (email: string, password: string, name: string) => Promise<{ success: boolean; error?: string }>;
    logout: () => Promise<void>;
    refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    const refreshUser = async () => {
        try {
            const res = await api.get('/auth/me');
            if (res.data.logged_in) {
                setUser(res.data.user);
            } else {
                setUser(null);
            }
        } catch {
            setUser(null);
        }
    };

    useEffect(() => {
        refreshUser().finally(() => setIsLoading(false));
    }, []);

    // Analytics: 사용자 식별 및 디버그 모드 설정
    useEffect(() => {
        if (user) {
            analytics.setDebugMode(!!user.is_admin);
            analytics.identify(user.id, {
                email: user.email,
                user_type: user.is_admin ? 'admin' : 'free',
                signup_date: user.created_at,
                current_level: user.level?.toString(),
                current_xp: user.xp,
            });
        }
    }, [user]);

    const login = async (email: string, password: string) => {
        try {
            const res = await api.post('/auth/login', { email, password });
            if (res.data.success) {
                // 로그인 성공 후 /auth/me에서 is_admin 포함 전체 정보 조회
                await refreshUser();
                // 로그인 성공 이벤트 트래킹
                analytics.loginSuccess(res.data.user?.id || email, 'email');
                return { success: true };
            }
            return { success: false, error: '로그인에 실패했습니다' };
        } catch (err: any) {
            return { success: false, error: err.response?.data?.detail || '로그인에 실패했습니다' };
        }
    };

    const register = async (email: string, password: string, name: string) => {
        try {
            const res = await api.post('/auth/register', { email, password, name });
            if (res.data.success) {
                setUser(res.data.user);
                // 회원가입 성공 이벤트 트래킹
                analytics.signUpCompleted(res.data.user?.id || email, 'email');
                return { success: true };
            }
            return { success: false, error: '회원가입에 실패했습니다' };
        } catch (err: any) {
            return { success: false, error: err.response?.data?.detail || '회원가입에 실패했습니다' };
        }
    };

    const logout = async () => {
        try {
            await api.post('/auth/logout', {});
        } catch {
            // ignore
        }
        setUser(null);
        analytics.reset();
    };

    return (
        <AuthContext.Provider value={{ user, isLoading, login, register, logout, refreshUser }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within AuthProvider');
    }
    return context;
}
