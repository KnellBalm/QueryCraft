// frontend/src/components/Skeleton.tsx
import './Skeleton.css';

interface SkeletonProps {
  variant?: 'text' | 'title' | 'card' | 'button' | 'avatar';
  width?: string;
  height?: string;
  className?: string;
}

export function Skeleton({ variant = 'text', width, height, className = '' }: SkeletonProps) {
  const variantClass = `skeleton-${variant}`;
  const style: React.CSSProperties = {};
  if (width) style.width = width;
  if (height) style.height = height;

  return <div className={`skeleton ${variantClass} ${className}`} style={style} />;
}

// 페이지 전체 로딩 스켈레톤
export function PageSkeleton() {
  return (
    <div className="skeleton-page">
      {/* 히어로 섹션 */}
      <div style={{ height: '200px', marginBottom: '2rem' }}>
        <Skeleton variant="card" height="200px" />
      </div>

      {/* 모드 카드 그리드 */}
      <Skeleton variant="title" width="200px" />
      <div className="skeleton-grid">
        <Skeleton variant="card" />
        <Skeleton variant="card" />
        <Skeleton variant="card" />
      </div>

      {/* 대시보드 패널 */}
      <div className="skeleton-row" style={{ marginTop: '2rem' }}>
        <div style={{ flex: 1 }}>
          <Skeleton variant="title" width="150px" />
          <Skeleton variant="text" />
          <Skeleton variant="text" width="90%" />
          <Skeleton variant="text" width="70%" />
        </div>
        <div style={{ flex: 1 }}>
          <Skeleton variant="title" width="150px" />
          <Skeleton variant="text" />
          <Skeleton variant="text" width="85%" />
        </div>
      </div>
    </div>
  );
}

// 헤더 우측 영역 스켈레톤 (로그인 버튼 자리)
export function HeaderSkeleton() {
  return (
    <div className="skeleton-header" style={{ marginLeft: 'auto' }}>
      <Skeleton variant="button" width="80px" height="32px" />
    </div>
  );
}
