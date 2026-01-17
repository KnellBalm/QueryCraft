// frontend/src/App.tsx
import { lazy } from 'react';
import { BrowserRouter, Routes, Route, NavLink, Link } from 'react-router-dom';
import { FloatingContact } from './components/FloatingContact';
import { LoginModal } from './components/LoginModal';
import { Onboarding, resetOnboarding } from './components/Onboarding';
import { Skeleton } from './components/Skeleton';
import { DropdownMenu } from './components/DropdownMenu';
import { DataCenterPage, MCPSandboxPage, AdaptiveTutorPage } from './components/PlaceholderPages';

// Code splitting: 각 페이지를 lazy load하여 초기 번들 크기 감소
const Workspace = lazy(() => import('./pages/Workspace').then(m => ({ default: m.Workspace })));
const Practice = lazy(() => import('./pages/Practice'));
const DailyChallenge = lazy(() => import('./pages/DailyChallenge'));  // NEW
const MainPage = lazy(() => import('./pages/MainPage').then(m => ({ default: m.MainPage })));
const MyPage = lazy(() => import('./pages/MyPage').then(m => ({ default: m.MyPage })));
const FutureLabDashboard = lazy(() => import('./pages/FutureLabDashboard').then(m => ({ default: m.FutureLabDashboard })));
const StatsPage = lazy(() => import('./pages/StatsPage'));
const AdminPage = lazy(() => import('./pages/AdminPage'));
import { ToastProvider } from './components/Toast';
import WeekendClosed from './components/WeekendClosed';
import { useEffect, useState, useMemo } from 'react';
import { statsApi } from './api/client';
import { initAnalytics, analytics } from './services/analytics';
import { useTheme } from './contexts/ThemeContext';
import { useAuth } from './contexts/AuthContext';
import { TrackProvider, useTrack } from './contexts/TrackContext';
import type { UserStats } from './types';
import './App.css';

function AppContent() {
  const [stats, setStats] = useState<UserStats | null>(null);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const { theme, toggleTheme } = useTheme();
  const { user, logout, isLoading } = useAuth();
  const { setTrack, isCore, isFuture } = useTrack();

  useEffect(() => {
    // Analytics 초기화
    initAnalytics();
  }, []);

  // 로그인 상태에 따른 stats 로드
  useEffect(() => {
    if (user) {
      statsApi.me().then(res => setStats(res.data)).catch(() => setStats(null));
    } else {
      setStats(null);
    }
  }, [user]);

  // SSO 로그인 성공 감지 (?login=success 파라미터)
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('login') === 'success' && user) {
      // SSO 로그인 성공 이벤트 트래킹
      // provider 정보는 user.id에서 추출 (google_xxx, kakao_xxx)
      const provider = user.id?.startsWith('google_') ? 'google' :
        user.id?.startsWith('kakao_') ? 'kakao' : 'email';
      analytics.loginSuccess(user.id, provider as 'google' | 'kakao' | 'email');
      // URL 정리 (파라미터 제거)
      window.history.replaceState({}, '', window.location.pathname);
    }
  }, [user]);
  // 주말 체크 (토요일: 6, 일요일: 0)
  const isWeekend = useMemo(() => {
    // 테스트 시 아래 값을 true로 설정하여 확인 가능
    const forceWeekend = false;
    if (forceWeekend) return true;

    const day = new Date().getDay();
    return day === 0 || day === 6;
  }, []);

  // 관리자 권한 확인 (주말 차단 우회용)
  const canAccessOnWeekend = user?.is_admin;

  return (
    <BrowserRouter>
      <Onboarding />
      <div className="app">
        <header className="header">
          <Link to="/" className="logo">📔QueryCraft</Link>

          {/* Track Switcher - Categories */}
          <div className="track-switcher">
            <Link
              to="/"
              className={`track-btn ${isCore ? 'active' : ''}`}
              onClick={() => setTrack('core')}
            >
              💼 Core Skills
            </Link>
            <Link
              to="/"
              className={`track-btn ${isFuture ? 'active' : ''}`}
              onClick={() => setTrack('future')}
            >
              🚀 Future Lab
            </Link>
          </div>

          <nav className="nav">
            {/* Core Skills Track 메뉴 */}
            {isCore && (
              <>
                <DropdownMenu label="오늘의 학습" icon="🏋️">
                  <NavLink to="/daily" className={({ isActive }) => isActive ? 'active' : ''}>
                    🗓️ Daily Challenge
                  </NavLink>
                  <NavLink to="/pa" className={({ isActive }) => isActive ? 'active' : ''}>
                    📅 오늘의 도전 (PA)
                  </NavLink>
                  <NavLink to="/stream" className={({ isActive }) => isActive ? 'active' : ''}>
                    📡 스트림 분석
                  </NavLink>
                </DropdownMenu>

                <NavLink to="/practice" className={({ isActive }) => isActive ? 'active' : ''}>
                  ♾️ 연습장
                </NavLink>

                <NavLink to="/stats" className={({ isActive }) => isActive ? 'active' : ''}>
                  🏆 리더보드
                </NavLink>

                <NavLink to="/datacenter" className={({ isActive }) => isActive ? 'active' : ''}>
                  📊 데이터 센터 <span className="badge-soon">준비중</span>
                </NavLink>
              </>
            )}

            {/* Future Lab Track 메뉴 */}
            {isFuture && (
              <>
                <NavLink to="/ailab" className={({ isActive }) => isActive ? 'active' : ''}>
                  🤖 AI Workspace
                </NavLink>
                
                <NavLink to="/rca" className={({ isActive }) => isActive ? 'active' : ''}>
                  🔍 RCA Simulator
                </NavLink>

                <NavLink to="/mcpsandbox" className={({ isActive }) => isActive ? 'active' : ''}>
                  🧪 MCP Sandbox <span className="badge-soon">준비중</span>
                </NavLink>

                <NavLink to="/tutor" className={({ isActive }) => isActive ? 'active' : ''}>
                  🎓 Adaptive Tutor <span className="badge-soon">준비중</span>
                </NavLink>
              </>
            )}
          </nav>
          <div className="user-stats">
            {user && stats && (
              <>
                <span className="streak">🔥 {stats.streak}일</span>
                <div className="xp-bar-container" title={`${stats.score || 0} / ${stats.next_level_threshold || 100} XP`}>
                  <div className="xp-info">
                    <span className="xp-label">{stats.level}</span>
                    <span className="xp-count">{stats.score || 0}/{stats.next_level_threshold || 0}</span>
                  </div>
                  <div className="xp-bar">
                    <div className="xp-fill" style={{ width: `${stats.level_progress || 0}%` }} />
                  </div>
                </div>
                <span className="correct">✅ {stats.correct}</span>
              </>
            )}
            <button
              className="theme-toggle"
              onClick={toggleTheme}
              aria-label="Toggle theme"
            >
              {theme === 'dark' ? '☀️' : '🌙'}
            </button>
            <button onClick={resetOnboarding} className="help-toggle" title="도움말 보기">
              ❓
            </button>
            {isLoading ? (
              <Skeleton variant="button" width="70px" height="28px" />
            ) : user ? (
              <div className="user-menu">
                <span className="user-name">👤 {user.nickname || user.name}</span>
                {user.is_admin && (
                  <Link to="/admin" className="btn-admin">⚙️ 관리자</Link>
                )}
                <Link to="/mypage" className="btn-mypage">마이페이지</Link>
                <button onClick={logout} className="btn-logout">로그아웃</button>
              </div>
            ) : (
              <button onClick={() => setShowLoginModal(true)} className="btn-login">로그인</button>
            )}
          </div>
        </header>

        <main className="main">
          <Routes>
            {isWeekend && !canAccessOnWeekend ? (
              <>
                {/* On weekends, show WeekendClosed by default but allow Practice mode */}
                <Route path="/practice" element={<Practice />} />
                <Route path="/mypage" element={<MyPage />} />
                <Route path="/admin" element={<AdminPage />} />
                <Route path="*" element={<WeekendClosed />} />
              </>
            ) : (
              <>
                <Route path="/" element={<MainPage />} />
                <Route path="/daily" element={<DailyChallenge />} />
                <Route path="/daily/:date" element={<DailyChallenge />} />
                <Route path="/pa" element={<Workspace dataType="pa" />} />
                <Route path="/stream" element={<Workspace dataType="stream" />} />
                <Route path="/stats" element={<StatsPage />} />
                <Route path="/datacenter" element={<DataCenterPage />} />
                <Route path="/practice" element={<Practice />} />
                <Route path="/rca" element={<Workspace dataType="rca" />} />
                <Route path="/mcpsandbox" element={<MCPSandboxPage />} />
                <Route path="/tutor" element={<AdaptiveTutorPage />} />
                <Route path="/future" element={<FutureLabDashboard />} />
                <Route path="/mypage" element={<MyPage />} />
                <Route path="/admin" element={<AdminPage />} />
              </>
            )}
          </Routes>
        </main>
        <FloatingContact />
        <LoginModal isOpen={showLoginModal} onClose={() => setShowLoginModal(false)} />
      </div>
    </BrowserRouter>
  );
}

const App: React.FC = () => {
  return (
    <TrackProvider>
      <ToastProvider>
        <AppContent />
      </ToastProvider>
    </TrackProvider>
  );
};

export default App;
