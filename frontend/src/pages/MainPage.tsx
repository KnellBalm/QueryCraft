// frontend/src/pages/MainPage.tsx
import { useEffect, useState, useMemo, memo } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useTrack } from '../contexts/TrackContext';
import { statsApi, problemsApi } from '../api/client';
import { useToast } from '../components/Toast';
import { Badge } from '../components/ui';
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

// 아케이드 대기실 스타일의 프로필 카드
const PlayerCard = memo(({ user, stats }: { user: User, stats: UserStats | null }) => {
    if (!user) return null;

    const nextLevelXP = stats?.next_level_threshold || 100;
    const currentXP = stats?.score || 0;
    const progress = Math.min(100, (currentXP / nextLevelXP) * 100);

    return (
        <div className="player-card">
            <div className="player-avatar">
                {user.nickname?.[0] || user.name?.[0] || '?'}
            </div>
            <div className="player-info">
                <h3 className="player-name">{user.nickname || user.name}</h3>
                <div className="player-level">Lv.{stats?.level || 1}</div>
            </div>
            <div className="player-xp">
                <div className="xp-bar">
                    <div className="xp-fill" style={{ width: `${progress}%` }} />
                </div>
                <span className="xp-text">{currentXP}/{nextLevelXP} XP</span>
            </div>
            <div className="player-stats">
                <div className="stat">
                    <span className="stat-icon">🔥</span>
                    <span className="stat-value">{stats?.streak || 0}</span>
                    <span className="stat-label">연속</span>
                </div>
                <div className="stat">
                    <span className="stat-icon">✅</span>
                    <span className="stat-value">{stats?.correct || 0}</span>
                    <span className="stat-label">정답</span>
                </div>
            </div>
        </div>
    );
});

// 히어로 섹션 (비로그인)
const LandingHero = memo(({ track }: { track: 'core' | 'future' }) => {
    return (
        <section className="arcade-hero">
            <div className="hero-scanline" />
            <div className="hero-content">
                <div className="hero-badge">
                    {track === 'core' ? '🕹️ SQL 아케이드' : '🛸 FUTURE LAB'}
                </div>
                <h1 className="arcade-title">
                    {track === 'core' ? (
                        <>QUERY<span className="neon">CRAFT</span></>
                    ) : (
                        <>FUTURE<span className="neon-alt">LAB</span></>
                    )}
                </h1>
                <p className="hero-sub">
                    {track === 'core'
                        ? '데이터 분석 실력을 레벨업하세요'
                        : 'AI 에이전트의 세계로 접속하세요'}
                </p>
                <p className="login-hint">로그인하여 게임을 시작하세요</p>
            </div>
        </section>
    );
});

// 아케이드 모드 선택 (세로 배치)
function ArcadeModesCore() {
    const [metadata, setMetadata] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        problemsApi.list('pa').then(res => {
            setMetadata(res.data.metadata);
        }).finally(() => {
            setLoading(false);
        });
    }, []);

    const productTypeLabel = useMemo(() => {
        if (!metadata) return '분석 환경 준비 중...';
        const typeMap: Record<string, string> = {
            'commerce': '커머스 (E-commerce)',
            'fintech': '핀테크 (Fintech)',
            'saas': 'SaaS (B2B)',
            'gaming': '게이밍 (Gaming)',
            'healthcare': '헬스케어 (Healthcare)'
        };
        return typeMap[metadata.product_type] || metadata.product_type;
    }, [metadata]);

    return (
        <div className="arcade-modes">
            <h2 className="modes-title">
                <span className="title-icon">🎮</span>
                게임 모드
            </h2>
            <div className="mode-list">
                {/* Unified Daily Challenge Card */}
                <Link to="/daily" className="arcade-mode-card mode-daily">
                    <div className="mode-glow" />
                    <div className="mode-btn-shine" />
                    <div className="mode-content">
                        <span className="mode-icon">📅</span>
                        <div className="mode-info">
                            <div className="mode-title-row">
                                <h3>오늘의 일일 분석</h3>
                                <span className="mode-badge">DAILY</span>
                            </div>
                            <p className="mode-desc">
                                {loading ? '환경 로딩 중...' : `오늘의 산업: ${productTypeLabel}`}
                            </p>
                            {!loading && metadata && (
                                <div className="mode-meta-tags" style={{ display: 'flex', gap: '8px', alignItems: 'center', marginTop: '12px' }}>
                                    <Badge variant="info">PA</Badge>
                                    <Badge variant="success">STREAM</Badge>
                                    <span style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', fontWeight: 600 }}>
                                        {metadata.company_name}
                                    </span>
                                </div>
                            )}
                        </div>
                    </div>
                    <span className="mode-arrow">▶</span>
                </Link>

                <Link to="/practice" className="arcade-mode-card mode-practice">
                    <div className="mode-glow" />
                    <div className="mode-content">
                        <span className="mode-icon">♾️</span>
                        <div className="mode-info">
                            <div className="mode-title-row">
                                <h3>SQL 연습장</h3>
                                <span className="mode-badge">∞</span>
                            </div>
                            <p>무제한 트레이닝 (자유 주제)</p>
                        </div>
                    </div>
                    <span className="mode-arrow">▶</span>
                </Link>
            </div>
        </div>
    );
}

function ArcadeModesFuture({ showToast }: { showToast: (msg: string, type: 'success' | 'error' | 'info' | 'warning') => void }) {
    return (
        <div className="arcade-modes future-modes">
            <h2 className="modes-title">
                <span className="title-icon">🛸</span>
                터미널 접속
            </h2>
            <div className="mode-list">
                <Link to="/ailab" className="arcade-mode-card mode-ai">
                    <div className="mode-glow" />
                    <div className="mode-content">
                        <span className="mode-icon">🤖</span>
                        <div className="mode-info">
                            <div className="mode-title-row">
                                <h3>AI 워크스페이스</h3>
                                <span className="mode-badge">NEW</span>
                            </div>
                            <p>에이전트 시뮬레이션</p>
                        </div>
                    </div>
                    <span className="mode-arrow">▶</span>
                </Link>

                <Link to="/rca" className="arcade-mode-card mode-rca">
                    <div className="mode-glow" />
                    <div className="mode-content">
                        <span className="mode-icon">🔍</span>
                        <div className="mode-info">
                            <div className="mode-title-row">
                                <h3>RCA 시뮬레이터</h3>
                                <span className="mode-badge">BETA</span>
                            </div>
                            <p>원인 분석 훈련</p>
                        </div>
                    </div>
                    <span className="mode-arrow">▶</span>
                </Link>

                <div
                    className="arcade-mode-card mode-mcp disabled"
                    onClick={() => showToast('MCP Sandbox 준비 중입니다! 🧪', 'info')}
                >
                    <div className="mode-content">
                        <span className="mode-icon">🧪</span>
                        <div className="mode-info">
                            <div className="mode-title-row">
                                <h3>MCP 샌드박스</h3>
                                <span className="mode-badge soon">SOON</span>
                            </div>
                            <p>도구 빌딩</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

// 리더보드 패널
const LeaderboardPanel = memo(({ leaderboard, currentUser }: { leaderboard: LeaderboardEntry[], currentUser?: User | null }) => {
    return (
        <div className="arcade-panel leaderboard-panel">
            <h2 className="panel-title">
                <span className="title-icon">🏆</span>
                랭킹
            </h2>
            <div className="leaderboard-list">
                {leaderboard.slice(0, 5).map((entry, idx) => (
                    <div
                        key={idx}
                        className={`rank-row ${entry.nickname === currentUser?.nickname ? 'me' : ''} rank-${entry.rank}`}
                    >
                        <span className="rank-medal">
                            {entry.rank === 1 ? '🥇' : entry.rank === 2 ? '🥈' : entry.rank === 3 ? '🥉' : `#${entry.rank}`}
                        </span>
                        <span className="rank-user">{entry.nickname}</span>
                        <span className="rank-score">{entry.correct}문제</span>
                    </div>
                ))}
                {leaderboard.length === 0 && (
                    <div className="empty-msg">아직 데이터가 없습니다</div>
                )}
            </div>
        </div>
    );
});

// 추천 문제 패널
const RecommendPanel = memo(({ problems }: { problems: Problem[] }) => {
    return (
        <div className="arcade-panel recommend-panel">
            <h2 className="panel-title">
                <span className="title-icon">✨</span>
                추천 문제
            </h2>
            <div className="recommend-list">
                {problems.map((p) => (
                    <Link
                        to={`/${p.data_type || 'pa'}?problem_id=${p.problem_id}`}
                        key={p.problem_id}
                        className={`recommend-item ${p.difficulty.toLowerCase()}`}
                    >
                        <span className={`difficulty-badge ${p.difficulty.toLowerCase()}`}>
                            {p.difficulty}
                        </span>
                        <span className="recommend-title">{p.title}</span>
                        <span className="recommend-arrow">→</span>
                    </Link>
                ))}
                {problems.length === 0 && (
                    <div className="empty-msg">추천 문제가 없습니다</div>
                )}
            </div>
        </div>
    );
});

// 활동 히트맵
const ActivityStrip = memo(({ history }: { history: ActivityLog[] }) => {
    const days = useMemo(() => {
        const result = [];
        for (let i = 13; i >= 0; i--) {
            const d = new Date();
            d.setDate(d.getDate() - i);
            const dateStr = d.toISOString().split('T')[0];
            const activity = history.find(h => h.session_date === dateStr);
            result.push({ date: dateStr, active: !!activity, correct: activity?.is_correct });
        }
        return result;
    }, [history]);

    return (
        <div className="activity-strip">
            <span className="strip-label">최근 활동</span>
            <div className="strip-grid">
                {days.map((day) => (
                    <div
                        key={day.date}
                        className={`strip-cell ${day.active ? (day.correct ? 'success' : 'fail') : 'empty'}`}
                        title={`${day.date}: ${day.active ? (day.correct ? '정답' : '시도') : '활동 없음'}`}
                    />
                ))}
            </div>
        </div>
    );
});

export function MainPage() {
    const { user } = useAuth();
    const { track, isCore } = useTrack();
    const { showToast } = useToast();

    const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
    const [recommendedProblems, setRecommendedProblems] = useState<Problem[]>([]);
    const [userStats, setUserStats] = useState<UserStats | null>(null);
    const [history, setHistory] = useState<ActivityLog[]>([]);

    useEffect(() => {
        async function loadData() {
            try {
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
    }, [user, track]);

    return (
        <div className="main-page arcade-lobby" data-track={track}>
            {/* 비로그인 시 히어로 */}
            {!user && <LandingHero track={track} />}

            {/* 메인 아케이드 레이아웃 */}
            <div className="arcade-container">
                {/* 왼쪽: 리더보드 */}
                <aside className="arcade-sidebar left">
                    <LeaderboardPanel leaderboard={leaderboard} currentUser={user} />
                </aside>

                {/* 중앙: 프로필 + 모드 선택 */}
                <main className="arcade-main">
                    {user && <PlayerCard user={user} stats={userStats} />}
                    {user && history.length > 0 && <ActivityStrip history={history} />}

                    {isCore ? (
                        <ArcadeModesCore />
                    ) : (
                        <ArcadeModesFuture showToast={showToast} />
                    )}
                </main>

                {/* 오른쪽: 추천 문제 */}
                <aside className="arcade-sidebar right">
                    <RecommendPanel problems={recommendedProblems} />
                </aside>
            </div>

            {/* AI Lab 소개 섹션 - 페이지 하단 */}
            <LabIntroSection />
        </div>
    );
}

// AI Lab 소개 섹션
function LabIntroSection() {
    return (
        <section className="lab-intro-section">
            <div className="lab-intro-header">
                <span className="lab-badge">ALPHA BUILDS</span>
                <h2>🤖 QueryCraft AI LAB</h2>
                <p>AI와 함께 더 빠르고 효율적으로 SQL 지식을 마스터하세요.</p>
            </div>

            <div className="lab-features-grid">
                <div className="lab-feature-card">
                    <div className="feature-icon">⌨️</div>
                    <h4>Natural Language to SQL</h4>
                    <p>복잡한 쿼리가 떠오르지 않을 땐 자연어로 질문하세요. AI가 즉시 PostgreSQL 쿼리로 변환해 줍니다.</p>
                </div>
                <div className="lab-feature-card">
                    <div className="feature-icon">📊</div>
                    <h4>AI Business Insight</h4>
                    <p>단순한 데이터 결과에서 비즈니스 가치를 발견하세요. AI가 결과를 분석하여 최적의 액션 플랜을 제안합니다.</p>
                </div>
                <div className="lab-feature-card">
                    <div className="feature-icon">🎯</div>
                    <h4>Adaptive Learning</h4>
                    <p>풀지 않은 문제와 틀렸던 유형을 분석하여 당신에게 가장 필요한 문제를 똑똑하게 추천합니다.</p>
                </div>
            </div>

            <div className="lab-upcoming">
                <h3>🚀 Upcoming Research</h3>
                <div className="upcoming-items">
                    <div className="upcoming-item">
                        <span>📡</span>
                        <span>Stream 분석 실시간 AI 보완</span>
                    </div>
                    <div className="upcoming-item">
                        <span>💬</span>
                        <span>SQL 코드 리뷰 및 성능 최적화 교정</span>
                    </div>
                </div>
            </div>
        </section>
    );
}
