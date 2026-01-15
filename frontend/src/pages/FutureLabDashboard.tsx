import { Link } from 'react-router-dom';
import './FutureLabDashboard.css';

export function FutureLabDashboard() {
    const features = [
        {
            icon: '🤖',
            title: 'AI Workspace',
            description: 'AI와 함께 SQL을 작성하고, 결과를 분석하여 인사이트를 얻으세요.',
            path: '/ailab',
            status: 'available',
            tags: ['Text-to-SQL', 'Insight Auto-gen']
        },
        {
            icon: '🔍',
            title: 'Crisis Simulator',
            description: '가상의 비즈니스 위기 상황을 시뮬레이션하고, 원인을 분석하세요.',
            path: '/rca',
            status: 'available',
            tags: ['RCA', 'Scenario Mode']
        },
        {
            icon: '🎓',
            title: 'Adaptive Tutor',
            description: '나의 약점을 분석하고 맞춤형 학습 경로를 제안받으세요.',
            path: '#',
            status: 'coming_soon',
            tags: ['Personalized', 'Recommendation']
        },
        {
            icon: '🔗',
            title: 'MCP Sandbox',
            description: 'AI 에이전트와 실시간 DB 연동 체험을 해보세요.',
            path: '#',
            status: 'coming_soon',
            tags: ['MCP', 'Agent']
        }
    ];

    return (
        <div className="future-lab-dashboard">
            <div className="future-lab-hero">
                <div className="hero-content">
                    <span className="hero-badge">🚀 FUTURE LAB</span>
                    <h1>AI 시대의 분석 환경을 미리 경험하세요</h1>
                    <p>
                        2026년의 데이터 분석가가 일하는 방식입니다.
                        AI와 협업하여 더 빠르고, 더 정확하게 인사이트를 도출하세요.
                    </p>
                </div>
            </div>

            <div className="features-grid">
                {features.map((feature, index) => (
                    <Link
                        to={feature.path}
                        key={index}
                        className={`feature-card ${feature.status === 'coming_soon' ? 'coming-soon' : ''}`}
                        onClick={(e) => feature.status === 'coming_soon' && e.preventDefault()}
                    >
                        <div className="feature-icon">{feature.icon}</div>
                        <h3>{feature.title}</h3>
                        <p>{feature.description}</p>
                        <div className="feature-tags">
                            {feature.tags.map((tag, i) => (
                                <span key={i} className="feature-tag">{tag}</span>
                            ))}
                        </div>
                        {feature.status === 'coming_soon' && (
                            <span className="coming-soon-badge">Coming Soon</span>
                        )}
                    </Link>
                ))}
            </div>

            <div className="future-lab-info">
                <h2>🎯 왜 Future Lab인가요?</h2>
                <div className="info-cards">
                    <div className="info-card">
                        <span className="info-icon">⚡</span>
                        <h4>효율성 10배</h4>
                        <p>AI가 SQL 초안을 작성하고, 인사이트를 자동 도출합니다.</p>
                    </div>
                    <div className="info-card">
                        <span className="info-icon">🎯</span>
                        <h4>정확도 향상</h4>
                        <p>실시간 데이터 검증으로 오류 없는 분석이 가능합니다.</p>
                    </div>
                    <div className="info-card">
                        <span className="info-icon">📈</span>
                        <h4>커리어 준비</h4>
                        <p>AI 시대의 분석가 역량을 미리 체험하고 준비하세요.</p>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default FutureLabDashboard;
