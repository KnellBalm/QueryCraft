// frontend/src/pages/DailyChallenge.tsx
/**
 * DailyChallenge - 통합 Daily Challenge 페이지 (워크스페이스 내장)
 * 문제를 선택하면 페이지 이동 없이 바로 쿼리 작성 및 제출 가능
 */
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { api, problemsApi, sqlApi } from '../api/client';
import { SQLEditor } from '../components/SQLEditor';
import { TableSchema } from '../components/TableSchema';
import { ResultTable } from '../components/ResultTable';
import ScenarioPanel from '../components/ScenarioPanel';
import { analytics } from '../services/analytics';
import type { TableSchema as Schema, SQLExecuteResponse, SubmitResponse } from '../types';
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
  is_completed?: boolean;
  is_correct?: boolean;
}

interface TableConfig {
  schema_name: string;
  table_name: string;
  full_name: string;
  purpose: string;
  row_count: number;
}

interface Scenario {
  date: string;
  company_name: string;
  company_description: string;
  product_type: string;
  situation: string;
  stake: string;
  data_period: {
    start: string;
    end: string;
  };
  table_configs: TableConfig[];
  data_story?: string | null;
  north_star: string;
  key_metrics: string[];
}

interface DailyChallengeData {
  version: string;
  scenario: Scenario;
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

  // 데이터 상태
  const [challenge, setChallenge] = useState<DailyChallengeData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showScenario, setShowScenario] = useState(true);
  const [tables, setTables] = useState<Schema[]>([]);

  // 워크스페이스 상태 (문제 선택 시 활성화)
  const [selectedProblem, setSelectedProblem] = useState<Problem | null>(null);
  const [sql, setSql] = useState('');
  const [result, setResult] = useState<SQLExecuteResponse | null>(null);
  const [submitResult, setSubmitResult] = useState<SubmitResponse | null>(null);
  const [executing, setExecuting] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [completedProblems, setCompletedProblems] = useState<Record<string, boolean>>({});

  // AI 도움 상태
  const [aiHelpUsed, setAiHelpUsed] = useState<Record<string, boolean>>({});
  const [aiHelpResult, setAiHelpResult] = useState<{ type: string; content: string } | null>(null);
  const [aiHelpLoading, setAiHelpLoading] = useState(false);
  const [showAiHelpMenu, setShowAiHelpMenu] = useState(false);

  const containerRef = useRef<HTMLDivElement>(null);

  // AI 메뉴 외부 클릭 처리
  useEffect(() => {
    if (!showAiHelpMenu) return;

    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      if (!target.closest('.ai-help-wrapper')) {
        setShowAiHelpMenu(false);
      }
    };

    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, [showAiHelpMenu]);

  // 데이터 로드
  const loadDailyChallenge = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const endpoint = date ? `/daily/${date}` : '/daily/latest';
      const [challengeRes, schemaRes] = await Promise.all([
        api.get(endpoint),
        problemsApi.schema('pa')
      ]);

      const data: DailyChallengeData = challengeRes.data;

      // 난이도 순 정렬 (easy → medium → hard)
      if (data.problems && data.problems.length > 0) {
        data.problems = [...data.problems].sort((a, b) => {
          const order = { easy: 1, medium: 2, hard: 3 };
          return (order[a.difficulty] || 2) - (order[b.difficulty] || 2);
        });
      }

      setChallenge(data);
      setTables(Array.isArray(schemaRes.data) ? schemaRes.data : []);

      // 완료 상태 초기화
      const completed: Record<string, boolean> = {};
      data.problems?.forEach(p => {
        if (p.is_completed) {
          completed[p.problem_id] = p.is_correct ?? false;
        }
      });
      setCompletedProblems(completed);

    } catch (err) {
      const error = err as { response?: { status?: number }; message?: string };
      if (error.response?.status === 404) {
        setError(`Daily Challenge를 찾을 수 없습니다 (${date || '최신'})`);
      } else if (error.response?.status === 503) {
        setError('데이터를 생성 중입니다. 잠시 후 다시 시도해주세요.');
      } else {
        setError(error.message || '데이터를 불러오는데 실패했습니다');
      }
    } finally {
      setLoading(false);
    }
  }, [date]);

  useEffect(() => {
    loadDailyChallenge();
  }, [loadDailyChallenge]);

  // 문제 선택
  const handleProblemClick = useCallback((problem: Problem) => {
    setSelectedProblem(problem);
    setSql('');
    setResult(null);
    setSubmitResult(null);
    setAiHelpResult(null);
    setShowAiHelpMenu(false);

    analytics.problemViewed(problem.problem_id, {
      difficulty: problem.difficulty,
      dataType: problem.problem_type,
      isDaily: true,
      topic: problem.topic
    });
  }, []);

  // 목록으로 돌아가기
  const handleBackToList = useCallback(() => {
    setSelectedProblem(null);
    setSql('');
    setResult(null);
    setSubmitResult(null);
    setAiHelpResult(null);
  }, []);

  // SQL 실행
  const handleExecute = useCallback(async () => {
    if (!sql.trim()) return;
    setExecuting(true);
    setResult(null);
    setSubmitResult(null);

    try {
      const res = await sqlApi.execute(sql);
      setResult(res.data);
      analytics.sqlExecuted(selectedProblem?.problem_id || 'unknown', {
        sql,
        hasError: !res.data.success,
        errorMessage: res.data.error,
        dbEngine: 'postgres'
      });
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setResult({ success: false, error: errorMessage });
    }
    setExecuting(false);
  }, [sql, selectedProblem]);

  // 제출
  const handleSubmit = useCallback(async () => {
    if (!sql.trim() || !selectedProblem) return;
    setSubmitting(true);
    setSubmitResult(null);

    try {
      const res = await sqlApi.submit(
        selectedProblem.problem_id,
        sql,
        selectedProblem.problem_type
      );
      setSubmitResult(res.data);

      // 완료 상태 업데이트
      setCompletedProblems(prev => ({
        ...prev,
        [selectedProblem.problem_id]: res.data.is_correct
      }));

      analytics.problemSubmitted(selectedProblem.problem_id, {
        isCorrect: res.data.is_correct,
        difficulty: selectedProblem.difficulty,
        dataType: selectedProblem.problem_type
      });
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setSubmitResult({ is_correct: false, feedback: errorMessage });
    }
    setSubmitting(false);
  }, [sql, selectedProblem]);

  // AI 도움
  const handleAiHelp = useCallback(async (helpType: 'hint' | 'solution') => {
    if (!selectedProblem || aiHelpUsed[selectedProblem.problem_id]) return;
    setAiHelpLoading(true);
    setShowAiHelpMenu(false);
    setAiHelpResult(null);

    try {
      const res = await sqlApi.aiHelp(
        selectedProblem.problem_id,
        helpType,
        sql,
        0,
        selectedProblem.problem_type
      );
      setAiHelpResult(res.data);
      setAiHelpUsed(prev => ({ ...prev, [selectedProblem.problem_id]: true }));
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setAiHelpResult({ type: 'error', content: `AI 도움 요청 실패: ${errorMessage}` });
    }
    setAiHelpLoading(false);
  }, [selectedProblem, aiHelpUsed, sql]);

  // 헬퍼 함수
  const getDifficultyIcon = (difficulty: string) => {
    const icons = { easy: '🟢', medium: '🟡', hard: '🔴' };
    return icons[difficulty as keyof typeof icons] || '⚪';
  };

  const getTypeIcon = (type: string) => type === 'pa' ? '🔢' : '📈';

  const getStatusIcon = (problemId: string) => {
    if (completedProblems[problemId] === true) return '✅';
    if (completedProblems[problemId] === false) return '❌';
    return '⬜';
  };

  // 로딩 상태
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

  // 에러 상태
  if (error) {
    return (
      <div className="daily-challenge-page">
        <div className="error-container">
          <h2>📅 Daily Challenge를 준비 중입니다</h2>
          <p>{error}</p>
          <p className="error-hint">매일 오전 10시(KST)에 새로운 Daily Challenge가 생성됩니다.</p>
          <div className="error-buttons">
            <button onClick={() => window.location.reload()} className="btn-primary">
              🔄 새로고침
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!challenge) return null;

  // 워크스페이스 모드 (문제 선택됨)
  if (selectedProblem) {
    return (
      <div className="daily-challenge-page workspace-mode" ref={containerRef}>
        {/* 상단 헤더 */}
        <div className="workspace-header">
          <button className="back-btn" onClick={handleBackToList}>
            ← 문제 목록
          </button>
          <div className="problem-nav">
            {challenge.problems.map((p, idx) => (
              <button
                key={p.problem_id}
                className={`nav-item ${p.problem_id === selectedProblem.problem_id ? 'active' : ''}`}
                onClick={() => handleProblemClick(p)}
                title={p.topic}
              >
                <span className="nav-status">{getStatusIcon(p.problem_id)}</span>
                <span className="nav-num">{idx + 1}</span>
                <span className="nav-diff">{getDifficultyIcon(p.difficulty)}</span>
              </button>
            ))}
          </div>
          <div className="header-date">{challenge.scenario.date}</div>
        </div>

        {/* 시나리오 (축소 가능) */}
        {showScenario && (
          <div className="scenario-mini">
            <div className="scenario-mini-header">
              <span>📖 {challenge.scenario.company_name}</span>
              <button onClick={() => setShowScenario(false)}>접기</button>
            </div>
            <p className="scenario-mini-text">{challenge.scenario.company_description?.slice(0, 150)}...</p>
          </div>
        )}
        {!showScenario && (
          <button className="show-scenario-btn" onClick={() => setShowScenario(true)}>
            📖 시나리오 보기
          </button>
        )}

        {/* 메인 워크스페이스 */}
        <div className="workspace-main">
          {/* 좌측: 문제 정보 */}
          <div className="workspace-left">
            <div className="problem-info-card">
              <div className="problem-info-header">
                <span className="problem-type-badge">
                  {getTypeIcon(selectedProblem.problem_type)} {selectedProblem.problem_type.toUpperCase()}
                </span>
                <span className={`difficulty-badge ${selectedProblem.difficulty}`}>
                  {getDifficultyIcon(selectedProblem.difficulty)} {selectedProblem.difficulty}
                </span>
              </div>
              <div className="problem-topic">{selectedProblem.topic}</div>

              <div className="slack-message-inline">
                <div className="slack-header-inline">
                  <span className="slack-avatar">👤</span>
                  <span className="slack-sender">{selectedProblem.requester}</span>
                </div>
                <div className="slack-content-inline">{selectedProblem.question}</div>
                {selectedProblem.context && (
                  <div className="slack-context-inline">ℹ️ {selectedProblem.context}</div>
                )}
              </div>

              {selectedProblem.expected_columns && (
                <div className="expected-columns">
                  <span className="label">결과 컬럼:</span>
                  {selectedProblem.expected_columns.map((col, i) => (
                    <code key={i}>{col}</code>
                  ))}
                </div>
              )}

              {selectedProblem.hint && (
                <details className="hint-details">
                  <summary>💬 힌트 보기</summary>
                  <p>{selectedProblem.hint}</p>
                </details>
              )}
            </div>

            {/* 스키마 정보 */}
            <div className="schema-section">
              <div className="schema-header">📋 테이블 스키마</div>
              <TableSchema tables={tables} />
            </div>
          </div>

          {/* 우측: 에디터 + 결과 */}
          <div className="workspace-right">
            <div className="editor-container">
              <div className="editor-top-bar">
                <span>SQL 에디터</span>
                <span className="shortcut-hint">Ctrl+Enter로 실행</span>
              </div>
              <SQLEditor
                value={sql}
                onChange={setSql}
                onExecute={handleExecute}
                height="200px"
                tables={tables}
              />
              <div className="action-bar">
                <button
                  className="btn-execute"
                  onClick={handleExecute}
                  disabled={executing || !sql.trim()}
                >
                  {executing ? '⏳ 실행 중...' : '▶️ 실행'}
                </button>

                <div className="ai-help-wrapper">
                  <button
                    className="btn-ai"
                    onClick={() => setShowAiHelpMenu(!showAiHelpMenu)}
                    disabled={aiHelpLoading || aiHelpUsed[selectedProblem.problem_id]}
                    title={aiHelpUsed[selectedProblem.problem_id] ? '이미 사용됨' : 'AI 도움'}
                  >
                    {aiHelpLoading ? '⏳' : '🤖'} AI
                    {!aiHelpUsed[selectedProblem.problem_id] && <span className="badge">1</span>}
                  </button>
                  {showAiHelpMenu && !aiHelpUsed[selectedProblem.problem_id] && (
                    <div className="ai-menu">
                      <button onClick={() => handleAiHelp('hint')}>💡 힌트</button>
                      <button onClick={() => handleAiHelp('solution')}>📝 정답</button>
                    </div>
                  )}
                </div>

                <button
                  className="btn-submit"
                  onClick={handleSubmit}
                  disabled={submitting || !sql.trim()}
                >
                  {submitting ? '⏳ 채점 중...' : '✅ 제출'}
                </button>
              </div>
            </div>

            {/* 결과 영역 */}
            <div className="daily-result-container">
              <div className="daily-result-header">
                📊 실행 결과
                {result?.execution_time_ms && (
                  <span className="exec-time">{result.execution_time_ms.toFixed(0)}ms</span>
                )}
              </div>

              <div className="daily-result-content">
                {/* AI 도움 결과 */}
                {aiHelpResult && (
                  <div className={`ai-result ${aiHelpResult.type === 'error' ? 'error' : ''}`}>
                    <div className="ai-result-title">🤖 AI 도움</div>
                    <pre>{aiHelpResult.content}</pre>
                  </div>
                )}

                {/* 제출 결과 */}
                {submitResult && (
                  <div className={`submit-result ${submitResult.is_correct ? 'correct' : 'wrong'}`}>
                    <div className="result-icon">
                      {submitResult.is_correct ? '✅ 정답입니다!' : '❌ 틀렸습니다'}
                    </div>
                    <div className="feedback">{submitResult.feedback}</div>
                    {submitResult.diff && (
                      <details className="diff-details">
                        <summary>상세 비교</summary>
                        <pre>{JSON.stringify(submitResult.diff, null, 2)}</pre>
                      </details>
                    )}
                  </div>
                )}

                {/* SQL 실행 결과 */}
                {result && result.success && result.data && (
                  <ResultTable columns={result.columns || []} data={result.data} />
                )}

                {result && !result.success && (
                  <div className="error-result">❌ {result.error}</div>
                )}

                {!result && !submitResult && !aiHelpResult && (
                  <div className="empty-result">SQL을 작성하고 실행 버튼을 누르세요</div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // 기본 모드: 문제 카드 그리드
  return (
    <div className="daily-challenge-page">
      <div className="daily-header">
        <div className="daily-title">
          <h1>🗓️ Daily Challenge</h1>
          <span className="daily-date">{challenge.scenario.date}</span>
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
          <h2>📝 오늘의 문제 ({challenge.metadata.total_problems}개)</h2>
          <div className="problem-stats">
            <span className="stat">PA: {challenge.metadata.pa_count}</span>
            <span className="stat">Stream: {challenge.metadata.stream_count}</span>
          </div>
        </div>

        <div className="problems-grid">
          {challenge.problems.map((problem, idx) => (
            <div
              key={problem.problem_id}
              className={`problem-card ${completedProblems[problem.problem_id] !== undefined ? 'attempted' : ''}`}
              onClick={() => handleProblemClick(problem)}
            >
              <div className="problem-header">
                <div className="problem-number">
                  {getStatusIcon(problem.problem_id) !== '⬜'
                    ? getStatusIcon(problem.problem_id)
                    : `#${idx + 1}`}
                </div>
                <div className="problem-badges">
                  <span className="type-badge">
                    {getTypeIcon(problem.problem_type)} {problem.problem_type?.toUpperCase() || 'PA'}
                  </span>
                  <span className={`difficulty-badge ${problem.difficulty || 'medium'}`}>
                    {getDifficultyIcon(problem.difficulty || 'medium')} {problem.difficulty || 'medium'}
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
                  {(problem.table_names || []).slice(0, 2).map((table, i) => (
                    <code key={i}>{table.split('.').pop()}</code>
                  ))}
                  {(problem.table_names || []).length > 2 && (
                    <span>+{(problem.table_names || []).length - 2}</span>
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
