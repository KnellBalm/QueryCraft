// frontend/src/api/client.ts
import axios from 'axios';

// 브라우저가 접속한 호스트를 기반으로 백엔드 URL 자동 설정
const getApiBase = () => {
    if (import.meta.env.VITE_API_URL) {
        return import.meta.env.VITE_API_URL;
    }
    // 개발 모드: Nginx 프록시(/api)를 사용하도록 상대 경로 반환
    // 운영 모드(Cloud Run): VITE_API_URL이 주입되므로 위에서 걸러짐
    if (typeof window !== 'undefined') {
        return '/api';
    }
    return 'http://localhost:15174';
};

const API_BASE = getApiBase();


export const api = axios.create({
    baseURL: API_BASE,
    withCredentials: true,  // 세션 쿠키 전송
    headers: {
        'Content-Type': 'application/json',
    },
});

// 문제 API
export const problemsApi = {
    list: (dataType: string, date?: string) =>
        api.get(`/problems/${dataType}`, { params: { target_date: date } }),

    detail: (dataType: string, problemId: string, date?: string) =>
        api.get(`/problems/${dataType}/${problemId}`, { params: { target_date: date } }),

    schema: (dataType: string) =>
        api.get(`/problems/schema/${dataType}`),
    
    recommend: (limit: number = 3) =>
        api.get('/problems/recommend', { params: { limit } }),
};

// SQL API
export const sqlApi = {
    execute: (sql: string, limit: number = 100) =>
        api.post('/sql/execute', { sql, limit }),

    submit: (problemId: string, sql: string, dataType: string = 'pa', note?: string) =>
        api.post('/sql/submit', { problem_id: problemId, sql, data_type: dataType, note }),

    hint: (problemId: string, sql: string, dataType: string = 'pa') =>
        api.post('/sql/hint', { problem_id: problemId, sql, data_type: dataType }),

    insight: (problemId: string, sql: string, results: any[], dataType: string = 'pa') =>
        api.post('/sql/insight', { problem_id: problemId, sql, results, data_type: dataType }),

    translate: (question: string, dataType: string = 'pa') =>
        api.post('/sql/translate', { question, data_type: dataType }),
};

// 통계 API
export const statsApi = {
    me: () => api.get('/stats/me'),
    history: (limit: number = 20, dataType?: string) =>
        api.get('/stats/history', { params: { limit, data_type: dataType } }),
    leaderboard: (limit: number = 20) =>
        api.get('/stats/leaderboard', { params: { limit } }),
    reset: () => api.delete('/stats/reset'),
};

// 관리자 API
export const adminApi = {
    status: () => api.get('/admin/status'),
    generateProblems: (dataType: string, force: boolean = false) =>
        api.post('/admin/generate-problems', { data_type: dataType, force }),
    refreshData: (dataType: string) =>
        api.post('/admin/refresh-data', { data_type: dataType }),
    resetSubmissions: () => api.post('/admin/reset-submissions'),
    datasetVersions: () => api.get('/admin/dataset-versions'),
    schedulerLogs: (lines: number = 50) => api.get('/admin/scheduler-logs', { params: { lines } }),
    schedulerStatus: () => api.get('/admin/scheduler-status'),
    getLogs: (category?: string, level?: string, limit: number = 100) =>
        api.get('/admin/logs', { params: { category, level, limit } }),
    getLogCategories: () => api.get('/admin/log-categories'),
    // 사용자 관리
    getUsers: () => api.get('/admin/users'),
    toggleAdmin: (userId: string) => api.patch(`/admin/users/${userId}/admin`),
    deleteUser: (userId: string) => api.delete(`/admin/users/${userId}`),
    // API 사용량
    getApiUsage: (days: number = 7, limit: number = 100) =>
        api.get('/admin/api-usage', { params: { days, limit } }),
    // 문제 파일 목록
    getProblemFiles: () => api.get('/admin/problem-files'),
    // 스케줄러 수동 실행
    runSchedulerJob: (jobType: string) => api.post('/admin/run-scheduler-job', null, { params: { job_type: jobType } }),
};

// 인증 API
export const authApi = {
    me: () => api.get('/auth/me'),
    logout: () => api.post('/auth/logout'),
    status: () => api.get('/auth/status'),
    googleLogin: () => `${API_BASE}/auth/google/login`,
    kakaoLogin: () => `${API_BASE}/auth/kakao/login`,
    deleteAccount: () => api.delete('/auth/account'),
};

// 무한 연습 모드 API
export const practiceApi = {
    generate: (dataType: string = 'pa') =>
        api.post('/practice/generate', { data_type: dataType }),
    submit: (problemId: string, sql: string, answerSql: string, difficulty: string, dataType: string = 'pa') =>
        api.post('/practice/submit', {
            problem_id: problemId,
            sql,
            answer_sql: answerSql,
            difficulty,
            data_type: dataType
        }),
};
