// frontend/src/pages/StatsPage.tsx
import { useEffect, useState } from 'react';
import { statsApi } from '../api/client';
import {
  Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer
} from 'recharts';
import { Skeleton } from '../components/Skeleton';
import './StatsPage.css';


export function StatsPage() {
  const [stats, setStats] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [skills, setSkills] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);


  useEffect(() => {
    async function loadStats() {
      try {
        const [statsRes, historyRes, skillsRes] = await Promise.all([
          statsApi.me(),
          statsApi.history(30),
          statsApi.skills()
        ]);
        setStats(statsRes.data);
        setHistory(historyRes.data);
        
        // 레이더 차트용 데이터 포맷팅
        const formattedSkills = (skillsRes.data.skills || []).map((s: any) => ({
          subject: s.category,
          A: s.score * 100, // 0~1 범위를 0~100으로 변환
          fullMark: 100,
          level: s.level
        }));
        setSkills(formattedSkills);
      } catch (e) {
        console.error('Stats load error:', e);
      }

      setLoading(false);
    }
    loadStats();
  }, []);

  if (loading) {
    return (
      <div className="stats-page">
        <Skeleton variant="title" width="200px" />
        <div className="stats-overview" style={{ display: 'flex', gap: '1rem' }}>
          <Skeleton variant="card" width="150px" height="100px" />
          <Skeleton variant="card" width="150px" height="100px" />
          <Skeleton variant="card" width="150px" height="100px" />
          <Skeleton variant="card" width="150px" height="100px" />
        </div>
      </div>
    );
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

      <div className="stats-main-content">
        <div className="stats-skills-chart">
          <h3>📊 역량 프로필 (Skill Radar)</h3>
          <div className="chart-container" style={{ width: '100%', height: 300 }}>
            <ResponsiveContainer>
              <RadarChart cx="50%" cy="50%" outerRadius="80%" data={skills}>
                <PolarGrid stroke="var(--border-color)" />
                <PolarAngleAxis dataKey="subject" tick={{ fill: 'var(--text-secondary)', fontSize: 12 }} />
                <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                <Radar
                  name="Skill Score"
                  dataKey="A"
                  stroke="#6366f1"
                  fill="#6366f1"
                  fillOpacity={0.6}
                />
              </RadarChart>
            </ResponsiveContainer>
          </div>
          <div className="skills-legend">
            {skills.map((s, i) => (
              <div key={i} className="skill-item">
                <span className="skill-name">{s.subject}</span>
                <span className="skill-level">Lv.{s.level}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="stats-progress-section">
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
          
          <div className="stats-weakness">
            <h3>⚠️ 집중 학습 추천</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
              최근 정답률이 낮은 <strong>{skills.sort((a,b) => a.A - b.A)[0]?.subject || '...'}</strong> 카테고리 문제를 추천합니다.
            </p>
            <button 
                onClick={() => window.location.href = '/practice'}
                className="btn-go-practice"
                style={{
                    marginTop: '1rem',
                    padding: '0.6rem 1rem',
                    backgroundColor: 'var(--accent-color)',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    fontWeight: 600
                }}
            >
              🚀 약점 보완하러 가기
            </button>
          </div>
        </div>
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

export default StatsPage;
