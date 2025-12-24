// frontend/src/App.tsx
import { BrowserRouter, Routes, Route, NavLink, Link } from 'react-router-dom';
import { Workspace } from './pages/Workspace';
import { FloatingContact } from './components/FloatingContact';
import { useEffect, useState } from 'react';
import { statsApi, adminApi } from './api/client';
import type { UserStats } from './types';
import './App.css';

function App() {
  const [stats, setStats] = useState<UserStats | null>(null);

  useEffect(() => {
    statsApi.me().then(res => setStats(res.data)).catch(() => { });
  }, []);

  return (
    <BrowserRouter>
      <div className="app">
        <header className="header">
          <Link to="/" className="logo">🎯 SQL Analytics Lab</Link>
          <nav className="nav">
            <NavLink to="/" end className={({ isActive }) => isActive ? 'active' : ''}>
              🧠 PA 연습
            </NavLink>
            <NavLink to="/stream" className={({ isActive }) => isActive ? 'active' : ''}>
              📊 Stream
            </NavLink>
            <NavLink to="/stats" className={({ isActive }) => isActive ? 'active' : ''}>
              📈 성적
            </NavLink>
            <NavLink to="/admin" className={({ isActive }) => isActive ? 'active' : ''}>
              ⚙️ 관리자
            </NavLink>
          </nav>
          <div className="user-stats">
            {stats && (
              <>
                <span className="streak">🔥 {stats.streak}일</span>
                <span className="level">{stats.level}</span>
                <span className="correct">✅ {stats.correct}</span>
              </>
            )}
          </div>
        </header>

        <main className="main">
          <Routes>
            <Route path="/" element={<Workspace dataType="pa" />} />
            <Route path="/stream" element={<Workspace dataType="stream" />} />
            <Route path="/stats" element={<StatsPage />} />
            <Route path="/admin" element={<AdminPage />} />
          </Routes>
        </main>
        <FloatingContact />
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
  const [status, setStatus] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [datasetVersions, setDatasetVersions] = useState<any[]>([]);

  const refreshStatus = () => {
    adminApi.status()
      .then(res => setStatus(res.data))
      .catch(() => { });

    // Dataset versions 가져오기
    adminApi.datasetVersions()
      .then(res => setDatasetVersions(res.data.versions || []))
      .catch(() => { });
  };

  useEffect(() => {
    refreshStatus();
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

      <section className="admin-section">
        <h2>⏰ 스케줄러 설정</h2>
        <div className="status-grid">
          <div className="status-item">
            <span>실행 주기</span>
            <span>매일 (24시간)</span>
          </div>
          <div className="status-item">
            <span>PA 데이터 갱신</span>
            <span>매일</span>
          </div>
          <div className="status-item">
            <span>PA 문제 생성</span>
            <span>매일</span>
          </div>
          <div className="status-item">
            <span>Stream 데이터 갱신</span>
            <span>매주 일요일</span>
          </div>
        </div>
      </section>

      <section className="admin-section">
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

      <section className="admin-section">
        <h2>📊 스케줄러 히스토리</h2>
        {status?.scheduler_sessions?.length > 0 ? (
          <table className="admin-table">
            <thead>
              <tr><th>날짜</th><th>상태</th><th>생성 시각</th></tr>
            </thead>
            <tbody>
              {status.scheduler_sessions.map((s: any) => (
                <tr key={s.session_date}>
                  <td>{s.session_date}</td>
                  <td className={s.status === 'GENERATED' ? 'ok' : ''}>{s.status}</td>
                  <td>{s.generated_at ? new Date(s.generated_at).toLocaleString() : '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p>스케줄러 기록이 없습니다.</p>
        )}
      </section>

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
        </div>
        {message && <p className="message">{message}</p>}
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
