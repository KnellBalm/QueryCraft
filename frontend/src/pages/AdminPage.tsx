// frontend/src/pages/AdminPage.tsx
import { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';
import { adminApi } from '../api/client';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../components/Toast';

// Modular Components
import { AdminOverview } from '../components/admin/AdminOverview';
import { AdminGeneration } from '../components/admin/AdminGeneration';
import { UserManagement } from '../components/admin/UserManagement';
import { SystemDiagnostics } from '../components/admin/SystemDiagnostics';

import './AdminPage.css';

type AdminTab = 'overview' | 'generation' | 'users' | 'diagnostics';

const AdminPage = () => {
  const { user, isLoading } = useAuth();
  const { showToast } = useToast();
  const [activeTab, setActiveTab] = useState<AdminTab>('overview');
  const [status, setStatus] = useState<any>(null);
  const [problemFiles, setProblemFiles] = useState<any[]>([]);

  // Authentication Guard
  if (!isLoading && (!user || !user.is_admin)) {
    return <Navigate to="/" replace />;
  }

  const refreshData = async () => {
    try {
      const [statusRes, filesRes] = await Promise.all([
        adminApi.status(),
        adminApi.getProblemFiles()
      ]);
      setStatus(statusRes.data);
      setProblemFiles(filesRes.data.files || []);
    } catch (e) {
      console.error('Failed to fetch admin data', e);
    }
  };

  useEffect(() => {
    refreshData();
  }, []);

  const showMessage = (message: string, type: 'success' | 'error' = 'success') => {
    showToast(message, type);
  };

  const today = new Date().toISOString().split('T')[0];

  return (
    <div className="admin-page-container">
      <div className="admin-header">
        <div className="admin-title">
          <h1>⚙️ Central Command</h1>
          <p>QueryCraft 시스템 관리 및 운영 통제</p>
        </div>

        <nav className="admin-tabs">
          <button
            className={activeTab === 'overview' ? 'active' : ''}
            onClick={() => setActiveTab('overview')}
          >
            📊 대시보드
          </button>
          <button
            className={activeTab === 'generation' ? 'active' : ''}
            onClick={() => setActiveTab('generation')}
          >
            🚀 콘텐츠 생성
          </button>
          <button
            className={activeTab === 'users' ? 'active' : ''}
            onClick={() => setActiveTab('users')}
          >
            👥 사용자 관리
          </button>
          <button
            className={activeTab === 'diagnostics' ? 'active' : ''}
            onClick={() => setActiveTab('diagnostics')}
          >
            🛠️ 진단 로그
          </button>
        </nav>
      </div>

      <main className="admin-content">
        {activeTab === 'overview' && (
          <AdminOverview status={status} today={today} />
        )}

        {activeTab === 'generation' && (
          <AdminGeneration
            problemFiles={problemFiles}
            onRefresh={refreshData}
            onShowMessage={showMessage}
          />
        )}

        {activeTab === 'users' && (
          <UserManagement />
        )}

        {activeTab === 'diagnostics' && (
          <SystemDiagnostics />
        )}
      </main>
    </div>
  );
};

export default AdminPage;
