// frontend/src/components/ScenarioPanel.tsx
/**
 * ScenarioPanel - 비즈니스 시나리오 컨텍스트 표시
 */
import React from 'react';
import './ScenarioPanel.css';

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

interface ScenarioPanelProps {
  scenario: Scenario;
  onClose?: () => void;
}

const ScenarioPanel: React.FC<ScenarioPanelProps> = ({ scenario, onClose }) => {
  const productTypeEmoji: Record<string, string> = {
    commerce: '🛒',
    saas: '💼',
    fintech: '💳',
    content: '📰',
    community: '👥',
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('ko-KR', {
      month: 'short',
      day: 'numeric'
    });
  };

  const periodDays = Math.ceil(
    (new Date(scenario.data_period.end).getTime() - 
     new Date(scenario.data_period.start).getTime()) / 
    (1000 * 60 * 60 * 24)
  );

  return (
    <div className="scenario-panel">
      <div className="scenario-header">
        <div className="scenario-title">
          <span className="scenario-icon">{productTypeEmoji[scenario.product_type] || '🏢'}</span>
          <div>
            <h2>{scenario.company_name}</h2>
            <span className="product-type-badge">{scenario.product_type}</span>
          </div>
        </div>
        {onClose && (
          <button className="close-btn" onClick={onClose}>✕</button>
        )}
      </div>

      <div className="scenario-body">
        {/* 상황 설명 */}
        <div className="scenario-section">
          <h3>📋 상황</h3>
          <p className="scenario-situation">{scenario.situation}</p>
        </div>

        {/* Stake (중요도) */}
        <div className="scenario-section">
          <h3>🎯 의뢰 배경</h3>
          <p className="scenario-stake">{scenario.stake}</p>
        </div>

        {/* 분석 기간 */}
        <div className="scenario-section">
          <h3>📅 분석 기간</h3>
          <div className="data-period">
            <span>{formatDate(scenario.data_period.start)}</span>
            <span className="period-arrow">→</span>
            <span>{formatDate(scenario.data_period.end)}</span>
            <span className="period-days">({periodDays}일)</span>
          </div>
        </div>

        {/* 테이블 정보 */}
        <div className="scenario-section">
          <h3>🗂️ 사용 가능한 테이블</h3>
          <div className="table-list">
            {scenario.table_configs.map((table, idx) => (
              <div key={idx} className="table-item">
                <div className="table-name">
                  <code>{table.full_name}</code>
                  <span className="table-rows">{table.row_count.toLocaleString()} rows</span>
                </div>
                <p className="table-purpose">{table.purpose}</p>
              </div>
            ))}
          </div>
        </div>

        {/* North Star & Key Metrics */}
        <div className="scenario-section">
          <h3>⭐ 핵심 지표</h3>
          <div className="metrics-container">
            <div className="north-star">
              <strong>North Star:</strong> {scenario.north_star}
            </div>
            <div className="key-metrics">
              {scenario.key_metrics.map((metric, idx) => (
                <span key={idx} className="metric-badge">{metric}</span>
              ))}
            </div>
          </div>
        </div>

        {/* 회사 설명 */}
        <div className="scenario-section company-desc">
          <p>{scenario.company_description}</p>
        </div>
      </div>
    </div>
  );
};

export default ScenarioPanel;
