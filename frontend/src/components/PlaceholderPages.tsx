// frontend/src/components/PlaceholderPages.tsx
import './PlaceholderPages.css';

export function DataCenterPage() {
  return (
    <div className="placeholder-page">
      <h1>📊 Data Center</h1>
      <p>전체 데이터 스키마 탐색 및 메타데이터 관리 서비스 준비 중입니다.</p>
      <div className="coming-soon-art">🏗️</div>
    </div>
  );
}

export function MCPSandboxPage() {
  return (
    <div className="placeholder-page">
      <h1>🧪 MCP Sandbox</h1>
      <p>Model Context Protocol(MCP) 기반의 AI 에이전트 도구 개발 환경 준비 중입니다.</p>
      <div className="coming-soon-art">🧪</div>
    </div>
  );
}

export function AdaptiveTutorPage() {
  return (
    <div className="placeholder-page">
      <h1>🎓 Adaptive Tutor</h1>
      <p>사용자 수준별 맞춤형 SQL/분석 학습 가이드 서비스 준비 중입니다.</p>
      <div className="coming-soon-art">🤖</div>
    </div>
  );
}
