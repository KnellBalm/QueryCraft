// frontend/src/pages/MainPage.tsx
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { statsApi } from '../api/client';
import './MainPage.css';

interface LeaderboardEntry {
    rank: number;
    nickname: string;
    correct: number;
    streak: number;
    level: string;
}

export function MainPage() {
    const { user } = useAuth();
    const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadLeaderboard();
    }, []);

    const loadLeaderboard = async () => {
        try {
            const res = await statsApi.leaderboard();
            setLeaderboard(Array.isArray(res.data) ? res.data : []);
        } catch (err) {
            console.error('Failed to load leaderboard:', err);
            setLeaderboard([]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="main-page">
            {/* 풀스크린 히어로 */}
            <section className="hero-section">
                <div className="hero-background" />
                <div className="hero-inner">
                    <h1>QueryCraft</h1>
                    <p className="hero-tagline">
                        데이터 분석 실력을 키우는<br />
                        가장 효과적인 방법
                    </p>
                    {user ? (
                        <Link to="/pa" className="cta-button">
                            오늘의 문제 시작하기
                        </Link>
                    ) : (
                        <p className="cta-hint">로그인하고 학습을 시작하세요</p>
                    )}
                </div>
            </section>

            {/* 모드 선택 - 풀폭 카드 */}
            <section className="modes-section">
                <Link to="/pa" className="mode-card mode-pa">
                    <div className="mode-icon">🧠</div>
                    <div className="mode-info">
                        <h3>PA 연습</h3>
                        <p>Product Analytics 실전 문제</p>
                    </div>
                    <span className="mode-badge">Daily</span>
                </Link>
                <Link to="/stream" className="mode-card mode-stream">
                    <div className="mode-icon">📊</div>
                    <div className="mode-info">
                        <h3>스트림 연습</h3>
                        <p>Real-time 스트리밍 데이터 분석</p>
                    </div>
                    <span className="mode-badge">Live</span>
                </Link>
                <Link to="/practice" className="mode-card mode-practice">
                    <div className="mode-icon">🎯</div>
                    <div className="mode-info">
                        <h3>무한 연습</h3>
                        <p>AI가 만드는 무제한 문제</p>
                    </div>
                    <span className="mode-badge">∞</span>
                </Link>
            </section>

            {/* 리더보드 + 팁 */}
            <section className="dashboard-section">
                <div className="dashboard-card leaderboard-card">
                    <h2>🏆 리더보드</h2>
                    {loading ? (
                        <div className="loading-placeholder">불러오는 중...</div>
                    ) : leaderboard.length === 0 ? (
                        <div className="empty-placeholder">
                            <p>아직 기록이 없습니다</p>
                            <span>첫 번째로 기록을 남겨보세요!</span>
                        </div>
                    ) : (
                        <ul className="leaderboard-list">
                            {leaderboard.slice(0, 5).map((entry, idx) => (
                                <li key={idx} className={entry.nickname === user?.nickname ? 'is-me' : ''}>
                                    <span className="rank">
                                        {entry.rank === 1 ? '🥇' : entry.rank === 2 ? '🥈' : entry.rank === 3 ? '🥉' : entry.rank}
                                    </span>
                                    <span className="name">{entry.nickname}</span>
                                    <span className="score">{entry.correct} solved</span>
                                </li>
                            ))}
                        </ul>
                    )}
                </div>

                <div className="dashboard-card tips-card">
                    <h2>💡 오늘의 팁</h2>
                    <div className="tip-item">
                        <h4>Window Functions</h4>
                        <p>ROW_NUMBER(), RANK()로 순위 계산</p>
                        <code>ROW_NUMBER() OVER (ORDER BY sales DESC)</code>
                    </div>
                    <div className="tip-item">
                        <h4>Date Aggregation</h4>
                        <p>DATE_TRUNC으로 시계열 집계</p>
                        <code>DATE_TRUNC('week', created_at)</code>
                    </div>
                </div>
            </section>

            {/* 하단 기능 안내 */}
            <section className="features-section">
                <div className="feature-item">
                    <span className="feature-icon">⏱</span>
                    <h4>Daily Problems</h4>
                    <p>매일 새로운 문제</p>
                </div>
                <div className="feature-item">
                    <span className="feature-icon">📈</span>
                    <h4>Progress Tracking</h4>
                    <p>학습 현황 추적</p>
                </div>
                <div className="feature-item">
                    <span className="feature-icon">🤖</span>
                    <h4>AI Hints</h4>
                    <p>막히면 힌트 요청</p>
                </div>
            </section>
        </div>
    );
}
