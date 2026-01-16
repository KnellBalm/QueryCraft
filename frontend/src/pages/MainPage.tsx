// frontend/src/pages/MainPage.tsx
import { useEffect, useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useTrack } from '../contexts/TrackContext';
import { statsApi, problemsApi } from '../api/client';
import { useToast } from '../components/Toast';
import type { Problem, UserStats } from '../types';
import './MainPage.css';

interface LeaderboardEntry {
    rank: number;
    nickname: string;
    correct: number;
    streak: number;
    level: string;
}

interface ActivityLog {
    session_date: string;
    is_correct: boolean;
}

// User definition matching AuthContext structure
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

function DailyBriefing({ user, stats, track }: { user: User, stats: UserStats | null, track: 'core' | 'future' }) {
    if (!user) return <LandingHero track={track} />;

    const nextLevelXP = stats?.next_level_threshold || 100;
    const currentXP = stats?.score || 0;
    const progress = Math.min(100, (currentXP / nextLevelXP) * 100);

    return (
        <section className="hero-section briefing-mode">
            <div className="hero-glow" />
            <div className="hero-grid" />
            <div className="briefing-container">
                <div className="briefing-header">
                    <span className="greeting">
                        {track === 'core' ? '👋 Welcome back,' : '🤖 System Online,'} <span className="highlight">{user.nickname || user.name}</span>
                    </span>
                    <span className="level-badge">Lv.{stats?.level || '1 Beginner'}</span>
                </div>

                <div className="xp-dashboard">
                    <div className="xp-info">
                        <span>EXP Progress</span>
                        <span>{currentXP} / {nextLevelXP} XP</span>
                    </div>
                    <div className="xp-bar-large">
                        <div className="xp-fill" style={{ width: `${progress}%` }} />
                    </div>
                </div>

                <div className="briefing-stats">
                    <div className="stat-box">
                        <span className="icon">🔥</span>
                        <div className="info">
                            <strong>{stats?.streak || 0} Days</strong>
                            <small>Current Streak</small>
                        </div>
                    </div>
                    <div className="stat-box">
                        <span className="icon">✅</span>
                        <div className="info">
                            <strong>{stats?.correct || 0} Solved</strong>
                            <small>Total Success</small>
                        </div>
                    </div>
                    <Link to={track === 'core' ? "/pa" : "/ailab"} className="continue-btn">
                        {track === 'core' ? '▶ Resume Training' : '▶ Access Terminal'}
                    </Link>
                </div>
            </div>
        </section>
    );
}

function LandingHero({ track }: { track: 'core' | 'future' }) {
    return (
        <section className="hero-section">
            <div className="hero-glow" />
            <div className="hero-grid" />
            <div className="hero-content">
                <div className="hero-badge">
                    {track === 'core' ? '🎮 SQL TRAINING ARENA' : '🦾 AI AGENT COMMAND CENTER'}
                </div>
                <h1>
                    {track === 'core' ? (
                        <>QUERY<span className="neon">CRAFT</span></>
                    ) : (
                        <>FUTURE<span className="neon">LAB</span></>
                    )}
                </h1>
                <p className="hero-sub">
                    {track === 'core'
                        ? <>Level up your data skills<br /><small>(* PostgreSQL supported)</small></>
                        : <>Build and simulate AI agents<br /><small>(* Experimental Features)</small></>
                    }
                </p>
                <p className="login-hint">Log in to start your journey</p>
            </div>
        </section>
    );
}

function ActivityHeatmap({ history }: { history: ActivityLog[] }) {
    // Generate last 14 days
    const days = useMemo(() => {
        const result = [];
        for (let i = 13; i >= 0; i--) {
            const d = new Date();
            d.setDate(d.getDate() - i);
            const dateStr = d.toISOString().split('T')[0];
            // Find activity for this day
            const activity = history.find(h => h.session_date === dateStr);
            result.push({ date: dateStr, active: !!activity, correct: activity?.is_correct });
        }
        return result;
    }, [history]);

    return (
        <div className="activity-heatmap">
            <h3>Recent Activity</h3>
            <div className="heatmap-grid">
                {days.map((day) => (
                    <div
                        key={day.date}
                        className={`heatmap-cell ${day.active ? (day.correct ? 'success' : 'fail') : 'empty'}`}
                        title={`${day.date}: ${day.active ? (day.correct ? 'Solved' : 'Attempted') : 'No Activity'}`}
                    />
                ))}
            </div>
        </div>
    );
}

export function MainPage() {
    const { user } = useAuth();
    const { track, isCore } = useTrack();
    const { showToast } = useToast();

    const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
    const [recommendedProblems, setRecommendedProblems] = useState<Problem[]>([]);
    const [userStats, setUserStats] = useState<UserStats | null>(null);
    const [history, setHistory] = useState<ActivityLog[]>([]);

    // loading state removed as it was unused in render,
    // or we can use it to show a spinner if we want.
    // For now, I'll remove it to fix the lint error.

    useEffect(() => {
        async function loadData() {
            try {
                // Parallel data loading
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                const promises: Promise<any>[] = [
                    statsApi.leaderboard(),
                    problemsApi.recommend(3)
                ];

                if (user) {
                    promises.push(statsApi.me());
                    promises.push(statsApi.history(30));
                }

                const results = await Promise.all(promises);

                setLeaderboard(Array.isArray(results[0]?.data) ? results[0].data : []);
                setRecommendedProblems(Array.isArray(results[1]?.data) ? results[1].data : []);

                if (user) {
                    setUserStats(results[2]?.data || null);
                    setHistory(Array.isArray(results[3]?.data) ? results[3].data : []);
                }
            } catch (err) {
                console.error('Failed to load main page data:', err);
            }
        }
        loadData();
    }, [user, track]); // Reload if track changes? Maybe recommendations change per track later.

    return (
        <div className="main-page" data-track={track}>
            {user && <DailyBriefing user={user} stats={userStats} track={track} />}
            {!user && <LandingHero track={track} />}

            {user && history.length > 0 && (
                <div className="heatmap-section">
                     <ActivityHeatmap history={history} />
                </div>
            )}

            {/* Modes Grid */}
            <section className="modes-section">
                <h2 className="section-title">
                    <span className="title-icon">{isCore ? '🕹️' : '📡'}</span>
                    SELECT MODE
                </h2>
                <div className="modes-grid">
                    {isCore ? (
                        <>
                            <Link to="/pa" className="mode-card mode-pa">
                                <div className="mode-glow" />
                                <span className="mode-icon">📈</span>
                                <h3>PA Analysis</h3>
                                <p>Product Analytics</p>
                                <span className="mode-tag">DAILY</span>
                            </Link>
                            <div className="mode-card mode-stream mode-disabled" onClick={() => showToast('Stream analysis coming soon! 📡', 'info')}>
                                <div className="mode-glow" />
                                <span className="mode-icon">📡</span>
                                <h3>Stream Data</h3>
                                <p>Real-time Events</p>
                                <span className="mode-tag">SOON</span>
                            </div>
                            <Link to="/practice" className="mode-card mode-practice">
                                <div className="mode-glow" />
                                <span className="mode-icon">♾️</span>
                                <h3>Practice Arena</h3>
                                <p>Unlimited Drill</p>
                                <span className="mode-tag">∞</span>
                            </Link>
                        </>
                    ) : (
                        <>
                            <Link to="/ailab" className="mode-card mode-ai">
                                <div className="mode-glow" />
                                <span className="mode-icon">🤖</span>
                                <h3>AI Workspace</h3>
                                <p>Agent Simulation</p>
                                <span className="mode-tag">NEW</span>
                            </Link>
                            <Link to="/rca" className="mode-card mode-rca">
                                <div className="mode-glow" />
                                <span className="mode-icon">🔍</span>
                                <h3>RCA Simulator</h3>
                                <p>Root Cause Analysis</p>
                                <span className="mode-tag">BETA</span>
                            </Link>
                             <div className="mode-card mode-mcp mode-disabled" onClick={() => showToast('MCP Sandbox coming soon! 🧪', 'info')}>
                                <div className="mode-glow" />
                                <span className="mode-icon">🧪</span>
                                <h3>MCP Sandbox</h3>
                                <p>Tool Building</p>
                                <span className="mode-tag">SOON</span>
                            </div>
                        </>
                    )}
                </div>
            </section>

            {/* Content Columns: Recommendations & Leaderboard */}
            <section className="dashboard-columns">
                <div className="column recommendations">
                    <h2 className="section-title small">
                        <span className="title-icon">✨</span>
                        FOR YOU
                    </h2>
                    <div className="rec-list">
                         {recommendedProblems.length > 0 ? (
                            recommendedProblems.map((p) => (
                                <Link
                                    to={`/${p.data_type || 'pa'}?problem_id=${p.problem_id}`}
                                    key={p.problem_id}
                                    className={`rec-item ${p.difficulty}`}
                                >
                                    <span className="rec-badge">{p.difficulty.toUpperCase()}</span>
                                    <div className="rec-info">
                                        <h4>{p.title}</h4>
                                        <span className="rec-sub">{p.data_type?.toUpperCase() || 'SQL'}</span>
                                    </div>
                                    <span className="rec-arrow">→</span>
                                </Link>
                            ))
                        ) : (
                            <div className="empty-msg">No recommendations available.</div>
                        )}
                    </div>
                </div>

                <div className="column leaderboard">
                    <h2 className="section-title small">
                        <span className="title-icon">🏆</span>
                        TOP AGENTS
                    </h2>
                    <div className="leaderboard-list">
                        {leaderboard.slice(0, 5).map((entry, idx) => (
                            <div key={idx} className={`rank-row ${entry.nickname === user?.nickname ? 'me' : ''}`}>
                                <span className="rank-num">#{entry.rank}</span>
                                <span className="rank-user">{entry.nickname}</span>
                                <span className="rank-xp">{entry.correct} Solved</span>
                            </div>
                        ))}
                        {leaderboard.length === 0 && <div className="empty-msg">No data yet.</div>}
                    </div>
                </div>
            </section>
        </div>
    );
}
