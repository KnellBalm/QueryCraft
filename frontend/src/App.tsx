// frontend/src/App.tsx
import { BrowserRouter, Routes, Route, NavLink, Link, Navigate } from 'react-router-dom';
import { Workspace } from './pages/Workspace';
import Practice from './pages/Practice';
import { MainPage } from './pages/MainPage';
import { MyPage } from './pages/MyPage';
import { FloatingContact } from './components/FloatingContact';
import { LoginModal } from './components/LoginModal';
import { Onboarding } from './components/Onboarding';
import { useEffect, useState } from 'react';
import { statsApi, adminApi } from './api/client';
import { initAnalytics } from './services/analytics';
import { useTheme } from './contexts/ThemeContext';
import { useAuth } from './contexts/AuthContext';
import type { UserStats } from './types';
import './App.css';

function App() {
  const [stats, setStats] = useState<UserStats | null>(null);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const { theme, toggleTheme } = useTheme();
  const { user, logout, isLoading } = useAuth();

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

  return (
    <BrowserRouter>
      <Onboarding />
      <div className="app">
        <header className="header">
          <Link to="/" className="logo">🎯 SQL Analytics Lab</Link>
          <nav className="nav">
            <NavLink to="/pa" className={({ isActive }) => isActive ? 'active' : ''}>
              🧠 PA 연습
            </NavLink>
            <NavLink to="/stream" className={({ isActive }) => isActive ? 'active' : ''}>
              📊 스트림 연습
            </NavLink>
            <NavLink to="/practice" className={({ isActive }) => isActive ? 'active' : ''}>
              🎯 무한 연습
            </NavLink>
          </nav>
          <div className="user-stats">
            {user && stats && (
              <>
                <span className="streak">🔥 {stats.streak}일</span>
                <span className="level">{stats.level}</span>
                <span className="correct">✅ {stats.correct}</span>
              </>
            )}
            <button onClick={toggleTheme} className="theme-toggle" title={theme === 'light' ? '다크 모드' : '라이트 모드'}>
              {theme === 'light' ? '🌙' : '☀️'}
            </button>
            {isLoading ? null : user ? (
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
            <Route path="/" element={<MainPage />} />
            <Route path="/pa" element={<Workspace dataType="pa" />} />
            <Route path="/stream" element={<Workspace dataType="stream" />} />
            <Route path="/stats" element={<StatsPage />} />
            <Route path="/practice" element={<Practice />} />
            <Route path="/mypage" element={<MyPage />} />
            <Route path="/admin" element={<AdminPage />} />
          </Routes>
        </main>
        <FloatingContact />
        <LoginModal isOpen={showLoginModal} onClose={() => setShowLoginModal(false)} />
      </div>
    </BrowserRouter>
  );
}

function StatsPage() {
  const [stats, setStats] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadStats() {
      try {
        const [statsRes, historyRes] = await Promise.all([
          statsApi.me(),
          statsApi.history(30)
        ]);
        setStats(statsRes.data);
        setHistory(historyRes.data);
      } catch (e) {
        console.error('Stats load error:', e);
      }
      setLoading(false);
    }
    loadStats();
  }, []);

  if (loading) {
    return <div className="stats-page"><p>로딩 중...</p></div>;
  }

  return (
    <div className="stats-page">
      <h1>📈 내 성적</h1>

      {stats && (
        <div className="stats-overview">
          <div className="stats-card">
            <div className="stats-icon">🔥</div>
            <div className="stats-value">{stats.streak}일</div>
            <div className="stats-label">연속 출석</div>
          </div>
          <div className="stats-card">
            <div className="stats-icon">{stats.level?.split(' ')[0] || '🌱'}</div>
            <div className="stats-value">{stats.level?.split(' ')[1] || 'Beginner'}</div>
            <div className="stats-label">현재 레벨</div>
          </div>
          <div className="stats-card">
            <div className="stats-icon">✅</div>
            <div className="stats-value">{stats.correct || 0}개</div>
            <div className="stats-label">정답 수</div>
          </div>
          <div className="stats-card">
            <div className="stats-icon">📊</div>
            <div className="stats-value">{stats.accuracy || 0}%</div>
            <div className="stats-label">정답률</div>
          </div>
        </div>
      )}

      <div className="stats-progress">
        <h3>🎯 다음 레벨까지</h3>
        <div className="progress-bar">
          <div
            className="progress-fill"
            style={{ width: `${Math.min(100, (stats?.correct || 0) / (stats?.next_level_threshold || 5) * 100)}%` }}
          />
        </div>
        <p>{stats?.correct || 0} / {stats?.next_level_threshold || 5} 문제</p>
      </div>

      <div className="stats-history">
        <h3>📝 최근 제출 이력</h3>
        {history.length > 0 ? (
          <table className="history-table">
            <thead>
              <tr>
                <th>날짜</th>
                <th>문제</th>
                <th>결과</th>
                <th>피드백</th>
              </tr>
            </thead>
            <tbody>
              {history.map((h: any, idx: number) => (
                <tr key={idx} className={h.is_correct ? 'correct' : 'incorrect'}>
                  <td>{h.session_date}</td>
                  <td>{h.problem_id}</td>
                  <td>{h.is_correct ? '✅ 정답' : '❌ 오답'}</td>
                  <td className="feedback">{h.feedback?.slice(0, 50) || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="empty">아직 제출 이력이 없습니다. 문제를 풀어보세요!</p>
        )}
      </div>
    </div>
  );
}

function AdminPage() {
  const { user, isLoading } = useAuth();

  // 로그인 안 했거나 관리자가 아니면 홈으로 리다이렉트
  if (!isLoading && (!user || !user.is_admin)) {
    return <Navigate to="/" replace />;
  }

  const [status, setStatus] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [datasetVersions, setDatasetVersions] = useState<any[]>([]);

  // 시스템 로그 뷰어
  const [systemLogs, setSystemLogs] = useState<any[]>([]);
  const [logCategory, setLogCategory] = useState<string>('');
  const [showSystemLogs, setShowSystemLogs] = useState(false);
  const logCategories = [
    { id: '', name: '전체', icon: '📋' },
    { id: 'problem_generation', name: '문제 생성', icon: '🤖' },
    { id: 'user_action', name: '사용자 액션', icon: '👤' },
    { id: 'scheduler', name: '스케줄러', icon: '⏰' },
    { id: 'system', name: '시스템', icon: '🖥️' },
    { id: 'api', name: 'API', icon: '🔌' }
  ];

  const loadSystemLogs = (category: string = '') => {
    adminApi.getLogs(category || undefined, undefined, 100)
      .then(res => setSystemLogs(res.data.logs || []))
      .catch(() => setSystemLogs([]));
  };

  // 사용자 관리
  const [users, setUsers] = useState<any[]>([]);
  const [showUsers, setShowUsers] = useState(true);  // 항상 열려있음

  const loadUsers = () => {
    adminApi.getUsers()
      .then(res => setUsers(res.data.users || []))
      .catch(() => setUsers([]));
  };

  // 페이지 로드 시 사용자 목록 자동 로드
  useEffect(() => {
    loadUsers();
  }, []);

  const handleToggleAdmin = async (userId: string) => {
    try {
      await adminApi.toggleAdmin(userId);
      loadUsers();
    } catch (e) {
      setMessage('권한 변경 실패');
    }
  };

  const handleDeleteUser = async (userId: string, email: string) => {
    if (window.confirm(`정말 ${email} 사용자를 삭제하시겠습니까?`)) {
      try {
        await adminApi.deleteUser(userId);
        loadUsers();
        setMessage('사용자가 삭제되었습니다');
      } catch (e) {
        setMessage('삭제 실패');
      }
    }
  };

  const refreshStatus = () => {
    adminApi.status()
      .then(res => setStatus(res.data))
      .catch(() => { });

    // Dataset versions 가져오기
    adminApi.datasetVersions()
      .then(res => setDatasetVersions(res.data.versions || []))
      .catch(() => { });
  };


  // API 사용량
  const [apiUsage, setApiUsage] = useState<any>(null);
  const [showApiUsage, setShowApiUsage] = useState(false);

  const loadApiUsage = () => {
    adminApi.getApiUsage(7, 50)
      .then(res => setApiUsage(res.data))
      .catch(() => setApiUsage(null));
  };

  // 문제 파일 목록
  const [problemFiles, setProblemFiles] = useState<any[]>([]);
  const [showProblemFiles, setShowProblemFiles] = useState(false);

  const loadProblemFiles = () => {
    adminApi.getProblemFiles()
      .then(res => setProblemFiles(res.data.files || []))
      .catch(() => setProblemFiles([]));
  };

  // 스케줄러 상태
  const [schedulerStatus, setSchedulerStatus] = useState<any>(null);

  const loadSchedulerStatus = () => {
    adminApi.schedulerStatus()
      .then(res => setSchedulerStatus(res.data))
      .catch(() => setSchedulerStatus(null));
  };

  const runSchedulerJob = async (jobType: string) => {
    setLoading(true);
    try {
      const res = await adminApi.runSchedulerJob(jobType);
      setMessage(res.data.message || '완료');
      loadSchedulerStatus();
      loadProblemFiles();
    } catch (e) {
      setMessage('실행 실패');
    }
    setLoading(false);
  };

  useEffect(() => {
    refreshStatus();
    loadApiUsage();
    loadProblemFiles();
    loadSchedulerStatus();
  }, []);

  const generateProblems = async () => {
    setLoading(true);
    setMessage('');
    try {
      const res = await adminApi.generateProblems('pa');
      setMessage(res.data.message || '완료');
      refreshStatus();
    } catch (e) {
      setMessage('오류 발생');
    }
    setLoading(false);
  };

  const generateStreamProblems = async () => {
    setLoading(true);
    setMessage('');
    try {
      const res = await adminApi.generateProblems('stream');
      setMessage(res.data.message || '완료');
      refreshStatus();
    } catch (e) {
      setMessage('오류 발생');
    }
    setLoading(false);
  };

  const refreshData = async (type: string) => {
    setLoading(true);
    setMessage('');
    try {
      const res = await adminApi.refreshData(type);
      setMessage(res.data.message || '완료');
      refreshStatus();
    } catch (e) {
      setMessage('오류 발생');
    }
    setLoading(false);
  };


  const today = new Date().toISOString().split('T')[0];

  return (
    <div className="admin-page">
      <h1>⚙️ 관리자 대시보드</h1>

      <section className="admin-section">
        <h2>� 시스템 연결 상태</h2>
        {status ? (
          <div className="status-grid">
            <div className="status-item">
              <span>PostgreSQL</span>
              <span className={status.postgres_connected ? 'ok' : 'error'}>
                {status.postgres_connected ? '✅ 연결됨' : '❌ 연결 안됨'}
              </span>
            </div>
            <div className="status-item">
              <span>DuckDB</span>
              <span className={status.duckdb_connected ? 'ok' : 'error'}>
                {status.duckdb_connected ? '✅ 연결됨' : '❌ 연결 안됨'}
              </span>
            </div>
          </div>
        ) : (
          <p>로딩 중...</p>
        )}
      </section>


      {/* 오늘의 문제 현황은 유지 */}      <section className="admin-section">
        <h2>� 오늘의 문제 현황 ({today})</h2>
        {status?.today_problems ? (
          <div className="problems-status">
            <div className="status-item">
              <span>문제 파일</span>
              <span className={status.today_problems.exists ? 'ok' : 'error'}>
                {status.today_problems.exists ? `✅ ${status.today_problems.count}개` : '❌ 없음'}
              </span>
            </div>
            {status.today_problems.difficulties && (
              <div className="difficulty-breakdown">
                {Object.entries(status.today_problems.difficulties).map(([diff, cnt]) => (
                  <span key={diff} className={`badge badge-${diff}`}>
                    {diff}: {cnt as number}개
                  </span>
                ))}
              </div>
            )}
          </div>
        ) : (
          <p className="error">오늘의 문제가 생성되지 않았습니다.</p>
        )}
      </section>


      {/* 스케줄러 히스토리는 스케줄러 관리 섹션에 통합됨 */}

      <section className="admin-section">
        <h2>�🔧 수동 작업</h2>
        <div className="action-buttons">
          <button onClick={generateProblems} disabled={loading}>
            🤖 PA 문제 생성
          </button>
          <button onClick={generateStreamProblems} disabled={loading}>
            🤖 Stream 문제 생성
          </button>
          <button onClick={() => refreshData('pa')} disabled={loading}>
            🔄 PA 데이터 갱신
          </button>
          <button onClick={() => refreshData('stream')} disabled={loading}>
            🔄 Stream 데이터 갱신
          </button>
          <button onClick={refreshStatus} disabled={loading}>
            🔃 상태 새로고침
          </button>
          <button
            onClick={async () => {
              if (window.confirm('⚠️ 모든 제출 기록이 삭제됩니다. 계속하시겠습니까?')) {
                setLoading(true);
                try {
                  const res = await adminApi.resetSubmissions();
                  // localStorage에서 완료 기록도 삭제
                  localStorage.removeItem('completed_pa');
                  localStorage.removeItem('completed_stream');
                  localStorage.removeItem('problem_ids_pa');
                  localStorage.removeItem('problem_ids_stream');
                  setMessage(res.data.message || '초기화 완료');
                  // 페이지 새로고침으로 모든 상태 리셋
                  setTimeout(() => window.location.reload(), 1000);
                } catch (e) {
                  setMessage('초기화 실패');
                }
                setLoading(false);
              }
            }}
            disabled={loading}
            style={{ backgroundColor: '#dc3545' }}
          >
            🗑️ 기록 초기화
          </button>
        </div>
        {message && <p className="message">{message}</p>}
      </section>

      <section className="admin-section">
        <h2>👥 사용자 관리</h2>
        <div style={{ marginBottom: '12px' }}>
          <button onClick={() => { setShowUsers(!showUsers); if (!showUsers) loadUsers(); }}>
            {showUsers ? '👥 사용자 목록 숨기기' : '👥 사용자 목록 보기'}
          </button>
        </div>
        {showUsers && (
          <div style={{ maxHeight: '400px', overflow: 'auto' }}>
            {users.length > 0 ? (
              <table className="admin-table" style={{ fontSize: '0.85rem' }}>
                <thead>
                  <tr>
                    <th>이메일</th>
                    <th>이름</th>
                    <th>닉네임</th>
                    <th>XP</th>
                    <th>레벨</th>
                    <th>관리자</th>
                    <th>가입일</th>
                    <th>관리</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((u: any) => (
                    <tr key={u.id}>
                      <td>{u.email}</td>
                      <td>{u.name}</td>
                      <td>{u.nickname || '-'}</td>
                      <td>{u.xp}</td>
                      <td>Lv.{u.level}</td>
                      <td>
                        <button
                          onClick={() => handleToggleAdmin(u.id)}
                          style={{
                            padding: '4px 8px',
                            fontSize: '0.75rem',
                            background: u.is_admin ? 'var(--success-color)' : 'var(--bg-tertiary)',
                            color: u.is_admin ? '#fff' : 'var(--text-primary)',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: 'pointer'
                          }}
                        >
                          {u.is_admin ? '✅ 관리자' : '일반'}
                        </button>
                      </td>
                      <td style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        {u.created_at ? new Date(u.created_at).toLocaleDateString() : '-'}
                      </td>
                      <td>
                        <button
                          onClick={() => handleDeleteUser(u.id, u.email)}
                          style={{
                            padding: '4px 8px',
                            fontSize: '0.75rem',
                            background: 'var(--error-color)',
                            color: '#fff',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: 'pointer'
                          }}
                        >
                          삭제
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '2rem' }}>
                등록된 사용자가 없습니다
              </div>
            )}
          </div>
        )}
      </section>

      <section className="admin-section">
        <h2>🗄️ 테이블 현황</h2>
        {status?.tables?.length > 0 ? (
          <table className="admin-table">
            <thead>
              <tr><th>테이블</th><th>행 수</th><th>컬럼 수</th></tr>
            </thead>
            <tbody>
              {status.tables.map((t: any) => (
                <tr key={t.table_name}>
                  <td>{t.table_name}</td>
                  <td>{t.row_count.toLocaleString()}</td>
                  <td>{t.column_count || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p>테이블 정보를 가져올 수 없습니다.</p>
        )}
      </section>

      {/* 문제 생성 이력 섹션 */}
      <section className="admin-section">
        <h2>📝 문제 생성 이력</h2>
        <div style={{ marginBottom: '12px' }}>
          <button onClick={() => { setShowProblemFiles(!showProblemFiles); loadProblemFiles(); }}>
            {showProblemFiles ? '📋 목록 숨기기' : '📋 파일 목록 보기'}
          </button>
        </div>
        {showProblemFiles && problemFiles.length > 0 && (
          <div style={{ maxHeight: '300px', overflow: 'auto' }}>
            <table className="admin-table" style={{ fontSize: '0.85rem' }}>
              <thead>
                <tr>
                  <th>타입</th>
                  <th>파일명</th>
                  <th>문제 수</th>
                  <th>크기</th>
                  <th>생성일시</th>
                </tr>
              </thead>
              <tbody>
                {problemFiles.map((f: any, i: number) => (
                  <tr key={i}>
                    <td>
                      <span style={{
                        padding: '2px 8px',
                        borderRadius: '4px',
                        fontSize: '0.75rem',
                        background: f.type === 'pa' ? '#3b82f6' : '#10b981',
                        color: 'white'
                      }}>
                        {f.type.toUpperCase()}
                      </span>
                    </td>
                    <td>{f.filename}</td>
                    <td>{f.problem_count}</td>
                    <td>{f.size_kb} KB</td>
                    <td>{new Date(f.created_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {showProblemFiles && problemFiles.length === 0 && (
          <p style={{ color: 'var(--text-muted)' }}>문제 파일이 없습니다.</p>
        )}
      </section>

      {/* 스케줄러 관리 섹션 */}
      <section className="admin-section">
        <h2>⏰ 스케줄러 관리</h2>
        <div className="status-grid" style={{ marginBottom: '16px' }}>
          <div className="status-item">
            <span>스케줄러 상태</span>
            <span className={schedulerStatus?.running ? 'ok' : 'error'}>
              {schedulerStatus?.running ? '🟢 실행 중' : '🔴 중지됨'}
            </span>
          </div>
        </div>

        {/* 스케줄 작업 목록 */}
        {schedulerStatus?.jobs && schedulerStatus.jobs.length > 0 && (
          <table className="admin-table" style={{ fontSize: '0.85rem', marginBottom: '16px' }}>
            <thead>
              <tr>
                <th>작업명</th>
                <th>다음 실행</th>
                <th>수동 실행</th>
              </tr>
            </thead>
            <tbody>
              {schedulerStatus.jobs.map((job: any, i: number) => (
                <tr key={i}>
                  <td>{job.name}</td>
                  <td>{job.next_run}</td>
                  <td>
                    <button
                      onClick={() => runSchedulerJob(job.id.replace('_generation', '').replace('_job', ''))}
                      disabled={loading}
                      style={{ padding: '4px 8px', fontSize: '0.8rem' }}
                    >
                      ▶️ 실행
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {/* 마지막 실행 시간 */}
        {schedulerStatus?.last_run_times && (
          <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            <p><strong>마지막 실행:</strong></p>
            <ul style={{ marginLeft: '20px' }}>
              <li>평일 작업: {schedulerStatus.last_run_times.weekday_job || '없음'}</li>
              <li>일요일 작업: {schedulerStatus.last_run_times.sunday_job || '없음'}</li>
              <li>정리 작업: {schedulerStatus.last_run_times.cleanup_job || '없음'}</li>
            </ul>
          </div>
        )}

        <div style={{ marginTop: '12px' }}>
          <button onClick={loadSchedulerStatus}>🔄 상태 새로고침</button>
        </div>
      </section>

      {/* API 사용량 섹션 */}
      <section className="admin-section">
        <h2>💰 AI API 사용량</h2>
        <div style={{ marginBottom: '12px' }}>
          <button onClick={() => { setShowApiUsage(!showApiUsage); loadApiUsage(); }}>
            {showApiUsage ? '📊 사용량 숨기기' : '📊 사용량 보기'}
          </button>
        </div>
        {showApiUsage && apiUsage && (
          <div>
            <div className="status-grid" style={{ marginBottom: '16px' }}>
              <div className="status-item">
                <span>총 호출 수</span>
                <span className="ok">{apiUsage.summary?.total_calls || 0}회</span>
              </div>
              <div className="status-item">
                <span>총 토큰</span>
                <span>{(apiUsage.summary?.total_tokens || 0).toLocaleString()}</span>
              </div>
              <div className="status-item">
                <span>예상 비용 (7일)</span>
                <span style={{ color: '#f59e0b', fontWeight: 'bold' }}>
                  ${apiUsage.summary?.estimated_cost_usd || 0}
                </span>
              </div>
              <div className="status-item">
                <span>입력 토큰</span>
                <span>{(apiUsage.summary?.input_tokens || 0).toLocaleString()}</span>
              </div>
              <div className="status-item">
                <span>출력 토큰</span>
                <span>{(apiUsage.summary?.output_tokens || 0).toLocaleString()}</span>
              </div>
            </div>
            {apiUsage.logs && apiUsage.logs.length > 0 && (
              <div style={{ maxHeight: '200px', overflow: 'auto' }}>
                <table className="admin-table" style={{ fontSize: '0.8rem' }}>
                  <thead>
                    <tr>
                      <th>시간</th>
                      <th>용도</th>
                      <th>모델</th>
                      <th>토큰</th>
                    </tr>
                  </thead>
                  <tbody>
                    {apiUsage.logs.slice(0, 20).map((log: any, i: number) => (
                      <tr key={i}>
                        <td>{new Date(log.timestamp).toLocaleString()}</td>
                        <td>{log.purpose}</td>
                        <td>{log.model}</td>
                        <td>{log.total_tokens}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </section>

      <section className="admin-section">
        <h2>📋 시스템 로그</h2>
        <div style={{ marginBottom: '12px', display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          {logCategories.map(cat => (
            <button
              key={cat.id}
              onClick={() => { setLogCategory(cat.id); loadSystemLogs(cat.id); setShowSystemLogs(true); }}
              style={{
                padding: '0.5rem 1rem',
                borderRadius: '6px',
                border: logCategory === cat.id ? '2px solid var(--accent-color)' : '1px solid var(--border-color)',
                background: logCategory === cat.id ? 'var(--accent-color)' : 'var(--bg-tertiary)',
                color: logCategory === cat.id ? '#fff' : 'var(--text-primary)',
                cursor: 'pointer',
                fontSize: '0.85rem'
              }}
            >
              {cat.icon} {cat.name}
            </button>
          ))}
        </div>
        {showSystemLogs && (
          <div style={{
            background: 'var(--bg-tertiary)',
            borderRadius: '8px',
            padding: '12px',
            maxHeight: '400px',
            overflow: 'auto'
          }}>
            {systemLogs.length > 0 ? (
              <table className="admin-table" style={{ fontSize: '0.85rem' }}>
                <thead>
                  <tr>
                    <th style={{ width: '140px' }}>시간</th>
                    <th style={{ width: '100px' }}>카테고리</th>
                    <th style={{ width: '60px' }}>레벨</th>
                    <th>메시지</th>
                    <th style={{ width: '100px' }}>소스</th>
                  </tr>
                </thead>
                <tbody>
                  {systemLogs.map((log: any) => (
                    <tr key={log.id} style={{
                      background: log.level === 'error' ? 'rgba(220,53,69,0.1)' :
                        log.level === 'warning' ? 'rgba(255,193,7,0.1)' : 'transparent'
                    }}>
                      <td style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        {log.created_at ? new Date(log.created_at).toLocaleString() : '-'}
                      </td>
                      <td>
                        <span style={{ fontSize: '0.75rem', padding: '2px 6px', borderRadius: '4px', background: 'var(--bg-secondary)' }}>
                          {log.category}
                        </span>
                      </td>
                      <td style={{
                        color: log.level === 'error' ? 'var(--error-color)' :
                          log.level === 'warning' ? 'var(--warning-color)' : 'var(--text-primary)'
                      }}>
                        {log.level}
                      </td>
                      <td>{log.message}</td>
                      <td style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{log.source || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '2rem' }}>
                카테고리를 선택하면 로그가 표시됩니다
              </div>
            )}
            <div style={{ marginTop: '8px', textAlign: 'right' }}>
              <button onClick={() => loadSystemLogs(logCategory)} style={{ fontSize: '0.8rem' }}>
                🔄 새로고침
              </button>
            </div>
          </div>
        )}
      </section>

      <section className="admin-section">
        <h2>📅 데이터셋 버전 이력</h2>
        {datasetVersions.length > 0 ? (
          <table className="admin-table">
            <thead>
              <tr><th>버전</th><th>생성일시</th><th>타입</th><th>기간</th><th>사용자 수</th><th>이벤트 수</th></tr>
            </thead>
            <tbody>
              {datasetVersions.map((v: any) => (
                <tr key={v.version_id}>
                  <td>{v.version_id}</td>
                  <td>{v.created_at ? new Date(v.created_at).toLocaleString() : '-'}</td>
                  <td>{v.generator_type || '-'}</td>
                  <td>{v.start_date && v.end_date ? `${v.start_date} ~ ${v.end_date}` : '-'}</td>
                  <td>{v.n_users?.toLocaleString() || '-'}</td>
                  <td>{v.n_events?.toLocaleString() || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p>데이터셋 버전 이력이 없습니다.</p>
        )}
      </section>
    </div>
  );
}


export default App;
