// frontend/src/pages/MainPage.tsx
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { statsApi } from '../api/client';
import { useToast } from '../components/Toast';
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
    const { showToast } = useToast();
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
            {/* 게임 스타일 히어로 */}
            <section className="hero-section">
                <div className="hero-glow" />
                <div className="hero-grid" />
                <div className="hero-content">
                    <div className="hero-badge">🎮 SQL TRAINING ARENA</div>
                    <h1>QUERY<span className="neon">CRAFT</span></h1>
                    <p className="hero-sub">레벨업하고 랭킹에 도전하세요<br /><small style={{ opacity: 0.8 }}>(* 현재 PostgreSQL 문법만 지원합니다)</small></p>
                    {user ? (
                        <Link to="/pa" className="play-button">
                            <span className="play-icon">▶</span>
                            PLAY NOW
                        </Link>
                    ) : (
                        <p className="login-hint">로그인하고 게임을 시작하세요</p>
                    )}
                </div>
            </section>

            {/* 게임 모드 선택 */}
            <section className="modes-section">
                <h2 className="section-title">
                    <span className="title-icon">🕹️</span>
                    SELECT MODE
                </h2>
                <div className="modes-grid">
                    <Link to="/pa" className="mode-card mode-pa">
                        <div className="mode-glow" />
                        <span className="mode-icon">📈</span>
                        <h3>PA 분석</h3>
                        <p>Product Analytics</p>
                        <span className="mode-tag">DAILY</span>
                    </Link>
                    <div
                        className="mode-card mode-stream mode-disabled"
                        onClick={() => showToast('스트림 분석은 준비 중입니다! 📡', 'info')}
                    >
                        <div className="mode-glow" />
                        <span className="mode-icon">📡</span>
                        <h3>스트림 분석</h3>
                        <p>Real-time Data</p>
                        <span className="mode-tag">준비 중</span>
                    </div>
                    <Link to="/practice" className="mode-card mode-practice">
                        <div className="mode-glow" />
                        <span className="mode-icon">♾️</span>
                        <h3>무한 연습</h3>
                        <p>AI Generated</p>
                        <span className="mode-tag">∞</span>
                    </Link>
                </div>
            </section>

            {/* 랭킹 & 팁 */}
            <section className="dashboard-section">
                <div className="panel ranking-panel">
                    <h2 className="panel-title">
                        <span>🏆</span> TOP PLAYERS
                    </h2>
                    {loading ? (
                        <div className="panel-loading">Loading...</div>
                    ) : leaderboard.length === 0 ? (
                        <div className="panel-empty">
                            <p>아직 플레이어가 없습니다</p>
                            <span>첫 번째 랭커가 되어보세요!</span>
                        </div>
                    ) : (
                        <ul className="ranking-list">
                            {leaderboard.slice(0, 5).map((entry, idx) => (
                                <li key={idx} className={`rank-item ${entry.nickname === user?.nickname ? 'is-me' : ''}`}>
                                    <span className="rank-pos">
                                        {entry.rank === 1 ? '🥇' : entry.rank === 2 ? '🥈' : entry.rank === 3 ? '🥉' : `#${entry.rank}`}
                                    </span>
                                    <span className="rank-name">{entry.nickname}</span>
                                    <span className="rank-score">{entry.correct} <small>SOLVED</small></span>
                                    <span className="rank-streak">🔥 {entry.streak}</span>
                                </li>
                            ))}
                        </ul>
                    )}
                </div>

                <div className="panel tips-panel">
                    <h2 className="panel-title">
                        <span>💡</span> QUICK TIPS <small style={{ fontWeight: 'normal', fontSize: '0.8rem', marginLeft: '5px' }}>(PostgreSQL)</small>
                    </h2>
                    <div className="tip-box">
                        <h4>Window Functions</h4>
                        <p>ROW_NUMBER()로 순위 계산</p>
                        <code>ROW_NUMBER() OVER (ORDER BY score DESC)</code>
                    </div>
                    <div className="tip-box">
                        <h4>Date Aggregation</h4>
                        <p>DATE_TRUNC으로 시계열 집계</p>
                        <code>DATE_TRUNC('week', created_at)</code>
                    </div>
                </div>
            </section>

            {/* 하단 스탯 */}
            <section className="stats-bar">
                <div className="stat-item">
                    <span className="stat-icon">⏱</span>
                    <div>
                        <strong>Daily Quest</strong>
                        <p>매일 새 문제</p>
                    </div>
                </div>
                <div className="stat-item">
                    <span className="stat-icon">📈</span>
                    <div>
                        <strong>Progress</strong>
                        <p>레벨 & 경험치</p>
                    </div>
                </div>
                <div className="stat-item">
                    <span className="stat-icon">🤖</span>
                    <div>
                        <strong>AI Hints</strong>
                        <p>막히면 힌트</p>
                    </div>
                </div>
            </section>
        </div>
    );
}
