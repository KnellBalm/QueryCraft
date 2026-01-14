// frontend/src/pages/AILab.tsx
import { Link } from 'react-router-dom';
import './AILab.css';

export function AILab() {
    return (
        <div className="ailab-page">
            <header className="ailab-header">
                <div className="ailab-badge">ALPHA BUILDS</div>
                <h1>🤖 QueryCraft AI LAB</h1>
                <p className="ailab-sub">AI와 함께 더 빠르고 효율적으로 SQL 지식을 마스터하세요.</p>
            </header>

            <div className="ailab-grid">
                {/* Text-to-SQL Section */}
                <div className="ailab-card featured">
                    <div className="card-icon">⌨️</div>
                    <div className="card-content">
                        <h3>Natural Language to SQL</h3>
                        <p>복잡한 쿼리가 떠오르지 않을 땐 자연어로 질문하세요. AI가 즉시 유효한 PostgreSQL 쿼리로 변환해 줍니다.</p>
                        <ul className="feature-list">
                            <li>PostgreSQL 스키마 기반 정확한 변환</li>
                            <li>워크스페이스 상단 바에서 즉시 사용 가능</li>
                            <li>SQL 초보자를 위한 최고의 파트너</li>
                        </ul>
                        <div className="card-footer">
                            <Link to="/pa" className="btn-try">지금 체험하기 →</Link>
                        </div>
                    </div>
                </div>

                {/* AI Insight Section */}
                <div className="ailab-card">
                    <div className="card-icon">📊</div>
                    <div className="card-content">
                        <h3>AI Business Insight</h3>
                        <p>단순한 데이터 결과에서 비즈니스 가치를 발견하세요. AI가 결과를 분석하여 실행 가능한 액션 플랜을 제안합니다.</p>
                        <ul className="feature-list">
                            <li>실행 결과 기반 인사이트 자동 추출</li>
                            <li>비즈니스 액션 플랜(Action Plan) 제안</li>
                            <li>전문 분석가 톤의 마크다운 리포트</li>
                        </ul>
                    </div>
                </div>

                {/* Personalized Recommendation Section */}
                <div className="ailab-card">
                    <div className="card-icon">🎯</div>
                    <div className="card-content">
                        <h3>Adaptive Learning</h3>
                        <p>풀지 않은 문제, 틀렸던 유형을 분석하여 당신에게 가장 필요한 문제를 똑똑하게 추천합니다.</p>
                        <ul className="feature-list">
                            <li>사용자별 맞춤 문제 추천 알고리즘</li>
                            <li>메인 페이지 'FOR YOU' 섹션에서 제공</li>
                            <li>지루할 틈 없는 최적의 학습 경로 제공</li>
                        </ul>
                        <div className="card-footer">
                            <Link to="/" className="btn-try">메인에서 확인 →</Link>
                        </div>
                    </div>
                </div>
            </div>

            <section className="ailab-future">
                <h2>🚀 준비 중인 연구 (Upcoming)</h2>
                <div className="future-grid">
                    <div className="future-item">
                        <span>📡</span>
                        <h4>Stream 분석 고도화</h4>
                        <p>대용량 로그 실시간 분석을 AI가 보조합니다.</p>
                    </div>
                    <div className="future-item">
                        <span>💬</span>
                        <h4>SQL 코드 리뷰</h4>
                        <p>당신이 작성한 SQL의 성능과 가독성을 교정합니다.</p>
                    </div>
                </div>
            </section>
        </div>
    );
}
