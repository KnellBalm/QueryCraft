// frontend/src/pages/DailyChallenge.tsx
/**
 * DailyChallenge - 통합 Daily Challenge 페이지
 */
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import ScenarioPanel from '../components/ScenarioPanel';
import './DailyChallenge.css';

interface Problem {
  problem_id: string;
  problem_type: 'pa' | 'stream';
  difficulty: 'easy' | 'medium' | 'hard';
  topic: string;
  requester: string;
  question: string;
  context?: string;
  expected_columns: string[];
  hint?: string;
  table_names: string[];
  scenario_id: string;
}

interface DailyChallengeData {
  version: string;
  scenario: any;
  problems: Problem[];
  metadata: {
    total_problems: number;
    pa_count: number;
    stream_count: number;
    difficulty_distribution: {
      easy: number;
      medium: number;
      hard: number;
    };
    created_at: string;
  };
}

const DailyChallenge: React.FC = () => {
  const { date } = useParams<{ date?: string }>();
  const navigate = useNavigate();

  const [challenge, setChallenge] = useState<DailyChallengeData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showScenario, setShowScenario] = useState(true);

  useEffect(() => {
    loadDailyChallenge();
  }, [date]);

  const loadDailyChallenge = async () => {
    setLoading(true);
    setError(null);

    try {
      const endpoint = date
        ? `/daily/${date}`
        : '/daily/latest';

      const response = await api.get(endpoint);
      setChallenge(response.data);
    } catch (err: any) {
      if (err.response?.status === 404) {
        setError(`Daily Challenge를 찾을 수 없습니다 (${date || '최신'})`);
      } else {
        setError(err.message || '데이터를 불러오는데 실패했습니다');
      }
    } finally {
      setLoading(false);
    }
  };

  const getDifficultyIcon = (difficulty: string) => {
    const icons = { easy: '🟢', medium: '🟡', hard: '🔴' };
    return icons[difficulty as keyof typeof icons] || '⚪';
  };

  const getTypeIcon = (type: string) => {
    return type === 'pa' ? '🔢' : '📈';
  };

  const handleProblemClick = (problem: Problem) => {
    // Workspace로 이동하면서 문제 선택 (dataType을 URL 경로에 포함)
    const dataType = problem.problem_type || 'pa';
    const params = new URLSearchParams({
      date: challenge?.scenario.date || '',
      problemId: problem.problem_id,
    });
    navigate(`/workspace/${dataType}?${params.toString()}`);
  };

  if (loading) {
    return (
      <div className="daily-challenge-page">
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Daily Challenge를 불러오는 중...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="daily-challenge-page">
        <div className="error-container">
          <h2>📅 Daily Challenge를 준비 중입니다</h2>
          <p>{error}</p>
          <p className="error-hint">매일 오전 10시(KST)에 새로운 Daily Challenge가 생성됩니다.</p>
          <div className="error-buttons">
            <button onClick={() => navigate('/pa')} className="btn-primary">
              📊 PA 문제 풀기
            </button>
            <button onClick={() => navigate('/practice')} className="btn-secondary">
              ♾️ 연습장으로 이동
            </button>
            <button onClick={() => window.location.reload()} className="btn-outline">
              🔄 새로고침
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!challenge) return null;

  return (
    <div className="daily-challenge-page">
      <div className="daily-header">
        <div className="daily-title">
          <h1>🗓️ Daily Challenge</h1>
          <span className="daily-date">{challenge.scenario?.date || ''}</span>
        </div>
        <button
          className="toggle-scenario-btn"
          onClick={() => setShowScenario(!showScenario)}
        >
          {showScenario ? '시나리오 숨기기' : '시나리오 보기'}
        </button>
      </div>

      {showScenario && (
        <ScenarioPanel
          scenario={challenge.scenario}
          onClose={() => setShowScenario(false)}
        />
      )}

      <div className="problems-section">
        <div className="problems-header">
          <h2>📝 오늘의 문제 ({challenge.metadata?.total_problems || 0}개)</h2>
          <div className="problem-stats">
            <span className="stat">PA: {challenge.metadata?.pa_count || 0}</span>
            <span className="stat">Stream: {challenge.metadata?.stream_count || 0}</span>
          </div>
        </div>

        <div className="problems-grid">
          {challenge.problems.map((problem, idx) => (
            <div
              key={problem.problem_id}
              className="problem-card"
              onClick={() => handleProblemClick(problem)}
            >
              <div className="problem-header">
                <div className="problem-number">#{idx + 1}</div>
                <div className="problem-badges">
                  <span className="type-badge">
                    {getTypeIcon(problem.problem_type)} {problem.problem_type.toUpperCase()}
                  </span>
                  <span className={`difficulty-badge ${problem.difficulty}`}>
                    {getDifficultyIcon(problem.difficulty)} {problem.difficulty}
                  </span>
                </div>
              </div>

              <div className="problem-body">
                <div className="problem-topic">{problem.topic}</div>
                <div className="problem-question">{problem.question}</div>
                <div className="problem-requester">
                  <strong>요청:</strong> {problem.requester}
                </div>
              </div>

              <div className="problem-footer">
                <div className="problem-tables">
                  {problem.table_names.slice(0, 2).map((table, i) => (
                    <code key={i}>{table.split('.').pop()}</code>
                  ))}
                  {problem.table_names.length > 2 && (
                    <span>+{problem.table_names.length - 2}</span>
                  )}
                </div>
                <button className="solve-btn">문제 풀기 →</button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default DailyChallenge;
