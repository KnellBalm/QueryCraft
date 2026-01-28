// frontend/src/components/PlaceholderPages.tsx
import { useEffect } from 'react';
import './PlaceholderPages.css';

export function DataCenterPage() {
  // 준비중 알림
  useEffect(() => {
    alert('준비중입니다');
  }, []);

  return (
    <div className="placeholder-page">
      <h1>📊 Data Center</h1>
      <p>전체 데이터 스키마 탐색 및 메타데이터 관리 서비스 준비 중입니다.</p>
      <div className="coming-soon-art">🏗️</div>
    </div>
  );
}

export function MCPSandboxPage() {
  // 준비중 알림
  useEffect(() => {
    alert('준비중입니다');
  }, []);

  return (
    <div className="placeholder-page">
      <h1>🧪 MCP Sandbox</h1>
      <p>Model Context Protocol(MCP) 기반의 AI 에이전트 도구 개발 환경 준비 중입니다.</p>
      <div className="coming-soon-art">🧪</div>
    </div>
  );
}
