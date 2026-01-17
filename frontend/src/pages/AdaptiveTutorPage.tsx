// frontend/src/pages/AdaptiveTutorPage.tsx
import { useEffect, useState } from 'react';
import { problemsApi, statsApi } from '../api/client';
import { Skeleton } from '../components/Skeleton';
import { analytics } from '../services/analytics';
import './AdaptiveTutorPage.css';

interface RecommendedProblem {
    problem_id: string;
    title: string;
    difficulty: string;
    topic: string;
    recommendation_reason: string;
}

export default function AdaptiveTutorPage() {
    const [recommendations, setRecommendations] = useState<RecommendedProblem[]>([]);
    const [skills, setSkills] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const loadTutorData = async () => {
            setLoading(true);
            try {
                const [recommendRes, skillsRes] = await Promise.all([
                    problemsApi.recommend(5),
                    statsApi.skills()
                ]);
                
                setRecommendations(recommendRes.data.problems || []);
                setSkills(skillsRes.data.skills || []);
                
                analytics.pageView('/adaptive-tutor', { data_type: 'adaptive' });
            } catch (error) {
                console.error('Failed to load tutor data:', error);
            } finally {
                setLoading(false);
            }
        };

        loadTutorData();
    }, []);

    const weakCategory = [...skills].sort((a, b) => a.score - b.score)[0];

    return (
        <div className="tutor-page">
            <header className="tutor-header">
                <div className="header-content">
                    <h1>🎓 Adaptive Tutor</h1>
                    <p>AI가 분석한 당신의 데이터 리터러시를 기반으로 개인화된 학습 여정을 제안합니다.</p>
                </div>
                {weakCategory && (
                    <div className="focus-badge">
                        <span className="label">오늘의 집중 학습</span>
                        <span className="value">#{weakCategory.category}</span>
                    </div>
                )}
            </header>

            <main className="tutor-main">
                <section className="recommendations-section">
                    <h2>🎯 맞춤형 추천 문제</h2>
                    {loading ? (
                        <div className="skeleton-grid">
                            {[1, 2, 3].map(i => <Skeleton key={i} height="150px" borderRadius="12px" />)}
                        </div>
                    ) : (
                        <div className="recommendation-grid">
                            {recommendations.length > 0 ? (
                                recommendations.map((prob) => (
                                    <div key={prob.problem_id} className="recommendation-card">
                                        <div className="card-header">
                                            <span className={`tag difficulty ${prob.difficulty}`}>{prob.difficulty}</span>
                                            <span className="tag topic">{prob.topic}</span>
                                        </div>
                                        <h3>{prob.title}</h3>
                                        <p className="reason">💡 {prob.recommendation_reason}</p>
                                        <button 
                                            className="btn-start"
                                            onClick={() => {
                                                analytics.track('Recommendation Clicked', { problem_id: prob.problem_id });
                                                window.location.href = `/pa-practice?id=${prob.problem_id}`;
                                            }}
                                        >
                                            문제 풀러 가기
                                        </button>
                                    </div>
                                ))
                            ) : (
                                <div className="empty-state">
                                    <p>아직 추천할 문제가 없습니다. 연습 모드에서 몇 문제를 먼저 풀어보세요!</p>
                                    <button onClick={() => window.location.href = '/practice'}>연습 모드 바로가기</button>
                                </div>
                            )}
                        </div>
                    )}
                </section>

                <section className="tutor-guide-section">
                    <h2>📖 학습 가이드</h2>
                    <div className="guide-grid">
                        <div className="guide-card">
                            <div className="icon">🛡️</div>
                            <h4>기초 다지기</h4>
                            <p>기본적인 SELECT, WHERE 절을 활용한 데이터 필터링 능력을 키웁니다.</p>
                        </div>
                        <div className="guide-card">
                            <div className="icon">⚔️</div>
                            <h4>복합 쿼리 마스터</h4>
                            <p>JOIN과 Subquery를 결합하여 복잡한 비즈니스 로직을 구현합니다.</p>
                        </div>
                        <div className="guide-card">
                            <div className="icon">💎</div>
                            <h4>분석적 사고</h4>
                            <p>Window Function과 Pivot을 사용하여 심화 통계 데이터를 추출합니다.</p>
                        </div>
                    </div>
                </section>
            </main>
        </div>
    );
}
