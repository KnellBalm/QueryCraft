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
            {/* 히어로 - 미니멀 대형 타이포 */}
            <section className="hero">
                <div className="hero-content">
                    <span className="hero-label">SQL Practice Platform</span>
                    <h1>
                        Master Data Analysis<br />
                        <span className="accent">One Query at a Time</span>
                    </h1>
                    <p className="hero-desc">
                        실전 SQL 문제를 매일 풀고, 데이터 분석 역량을 체계적으로 성장시키세요.
                    </p>
                    {!user ? (
                        <p className="hero-cta">로그인하고 학습을 시작하세요 →</p>
                    ) : (
                        <Link to="/pa" className="hero-button">
                            오늘의 문제 풀기 →
                        </Link>
                    )}
                </div>
            </section>

            {/* 모드 선택 - 에디토리얼 카드 */}
            <section className="modes-section">
                <div className="section-header">
                    <span className="section-number">01</span>
                    <h2>Practice Modes</h2>
                </div>
                <div className="modes-grid">
                    <Link to="/pa" className="mode-card">
                        <div className="mode-number">01</div>
                        <div className="mode-content">
                            <h3>PA 연습</h3>
                            <p>Product Analytics 실전 문제</p>
                            <span className="mode-tag">Daily</span>
                        </div>
                        <span className="mode-arrow">→</span>
                    </Link>
                    <Link to="/stream" className="mode-card">
                        <div className="mode-number">02</div>
                        <div className="mode-content">
                            <h3>스트림 연습</h3>
                            <p>Streaming 데이터 분석</p>
                            <span className="mode-tag">Real-time</span>
                        </div>
                        <span className="mode-arrow">→</span>
                    </Link>
                    <Link to="/practice" className="mode-card">
                        <div className="mode-number">03</div>
                        <div className="mode-content">
                            <h3>무한 연습</h3>
                            <p>AI가 생성하는 무제한 문제</p>
                            <span className="mode-tag">Infinite</span>
                        </div>
                        <span className="mode-arrow">→</span>
                    </Link>
                </div>
            </section>

            {/* 리더보드 & 팁 - 2컬럼 */}
            <div className="content-grid">
                {/* 리더보드 */}
                <section className="leaderboard-section">
                    <div className="section-header">
                        <span className="section-number">02</span>
                        <h2>Leaderboard</h2>
                    </div>
                    {loading ? (
                        <div className="loading-state">Loading...</div>
                    ) : leaderboard.length === 0 ? (
                        <div className="empty-state">
                            <p>아직 기록이 없습니다</p>
                            <span>첫 번째 문제를 풀어보세요</span>
                        </div>
                    ) : (
                        <div className="leaderboard-list">
                            {leaderboard.slice(0, 5).map((entry, idx) => (
                                <div
                                    key={idx}
                                    className={`leaderboard-item ${entry.nickname === user?.nickname ? 'is-me' : ''}`}
                                >
                                    <span className="lb-rank">
                                        {entry.rank === 1 ? '🥇' : entry.rank === 2 ? '🥈' : entry.rank === 3 ? '🥉' : entry.rank}
                                    </span>
                                    <span className="lb-name">{entry.nickname}</span>
                                    <span className="lb-stats">
                                        <span className="lb-correct">{entry.correct}</span>
                                        <span className="lb-streak">{entry.streak}d</span>
                                    </span>
                                </div>
                            ))}
                        </div>
                    )}
                </section>

                {/* SQL 팁 */}
                <section className="tips-section">
                    <div className="section-header">
                        <span className="section-number">03</span>
                        <h2>Today's Tip</h2>
                    </div>
                    <div className="tip-card">
                        <h4>Window Functions</h4>
                        <p>ROW_NUMBER(), RANK(), DENSE_RANK()로 순위를 계산하세요.</p>
                        <code>ROW_NUMBER() OVER (PARTITION BY category ORDER BY sales DESC)</code>
                    </div>
                    <div className="tip-card">
                        <h4>Date Functions</h4>
                        <p>DATE_TRUNC으로 시계열 데이터를 집계하세요.</p>
                        <code>DATE_TRUNC('month', created_at)</code>
                    </div>
                </section>
            </div>

            {/* 하단 특징 */}
            <section className="features-section">
                <div className="feature">
                    <span className="feature-icon">⏱</span>
                    <div>
                        <h4>Daily Problems</h4>
                        <p>매일 새로운 문제 제공</p>
                    </div>
                </div>
                <div className="feature">
                    <span className="feature-icon">📊</span>
                    <div>
                        <h4>Progress Tracking</h4>
                        <p>학습 현황 실시간 추적</p>
                    </div>
                </div>
                <div className="feature">
                    <span className="feature-icon">🤖</span>
                    <div>
                        <h4>AI Hints</h4>
                        <p>막히면 AI에게 힌트 요청</p>
                    </div>
                </div>
            </section>
        </div>
    );
}
