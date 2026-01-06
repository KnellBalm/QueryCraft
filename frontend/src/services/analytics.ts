// frontend/src/services/analytics.ts
/**
 * 이벤트 트래킹 서비스 - Mixpanel + GA4 (GTM) 통합
 * - 이벤트 네이밍: Title Case (동사 + 대상)
 * - Core Action: Problem Solved
 * - 환경 구분: env property
 * - GA4: GTM dataLayer를 통한 이벤트 전송
 */

// Mixpanel, PostHog, GA4 dataLayer 전역 타입 선언
declare global {
    interface Window {
        mixpanel?: {
            init: (token: string, config?: object) => void;
            track: (event: string, properties?: object) => void;
            identify: (userId: string) => void;
            reset: () => void;
            people: {
                set: (properties: object) => void;
                increment: (property: string, value?: number) => void;
            };
        };
        posthog?: {
            init: (key: string, config?: object) => void;
            capture: (event: string, properties?: object) => void;
            identify: (userId: string, properties?: object) => void;
            reset: () => void;
        };
        dataLayer?: Array<Record<string, any>>;
    }
}

// MVP 기준 필수 이벤트 (가이드 준수)
export type AnalyticsEvent =
    // 유입
    | 'Page Viewed'
    // 회원
    | 'Sign Up Completed'
    // 인증
    | 'Login Success'
    | 'Logout Completed'
    // 핵심 가치 (Core Action)
    | 'Problem Solved'  // ⭐ Core Action (정답 판정 시에만)
    // 문제 풀이 관련 (Funnel)
    | 'Problem Viewed'
    | 'Problem Attempted'
    | 'Problem Submitted'
    | 'Problem Failed'    // 오답 시점
    | 'Hint Requested'
    // SQL 관련
    | 'SQL Executed'      // 실행 시점
    | 'SQL Error Occurred' // 에러 발생 시점
    // 온보딩
    | 'Onboarding Started'
    | 'Onboarding Completed'
    | 'Onboarding Skipped'
    // 기타
    | 'Tab Changed'
    | 'Schema Viewed'
    | 'Contact Clicked';

// 환경 구분
const getEnvironment = (): 'local' | 'staging' | 'prod' => {
    const hostname = window.location.hostname;
    if (hostname === 'localhost' || hostname === '127.0.0.1') return 'local';
    if (hostname.includes('staging') || hostname.includes('test')) return 'staging';
    return 'prod';
};

// 이벤트 속성 타입
export interface EventProperties {
    // 공통 필수 (Mixpanel 기본 제공 외)
    timestamp?: string;
    page?: string;
    env?: 'local' | 'staging' | 'prod';

    // 문제 관련 필수 (Tracking Plan 준수)
    problem_id?: string;
    difficulty_level?: 'easy' | 'medium' | 'hard';
    topic_tags?: string | string[];
    is_daily_problem?: boolean;
    daily_issue_date?: string; // YYYY-MM-DD
    data_type?: 'pa' | 'stream' | 'practice' | string;

    // 시도/효율 (Attempt/Solve 관련)
    attempt_count?: number;      // 해당 문제에서 몇 번째 제출인지
    execution_count?: number;    // 해당 문제에서 몇 번째 실행인지
    time_spent_sec?: number;     // Viewed ~ Solved 까지 소요 시간 (초)
    result?: 'success' | 'fail';  // 제출 결과

    // SQL/Friction 관련
    sql_length?: number;
    sql_text?: string;
    error_type?: string;         // syntax, runtime, timeout 등
    error_message?: string;
    db_engine?: string;          // postgres, duckdb 등
    used_hint_before?: boolean;  // 정답 제출 전 힌트 사용 여부

    // 인증/프로필 관련
    auth_provider?: 'google' | 'kakao' | 'email';
    user_id?: string;
    is_new_user?: boolean;

    // 온보딩 관련
    step_skipped_at?: number;
    total_steps?: number;
    onboarding_step?: number;

    // 기타
    tab_name?: string;
    schema_name?: string;
    [key: string]: any;
}

// User Properties 타입 (Tracking Plan 권장)
export interface UserProperties {
    user_id: string;
    email?: string;
    user_type: 'free' | 'admin';
    signup_date?: string;
    signup_cohort_date?: string; // YYYY-MM-DD
    total_problems_solved?: number;
    current_level?: string;
    current_xp?: number;
    experience_level?: string; // 초보, 중수, 고수 등
}

class Analytics {
    private env: 'local' | 'staging' | 'prod';
    private startTime: number = Date.now();
    private attemptCounts: Record<string, number> = {};
    private executionCounts: Record<string, number> = {};
    private debugMode: boolean = false;

    constructor() {
        this.env = getEnvironment();
    }

    setDebugMode(enabled: boolean) {
        this.debugMode = enabled;
    }

    private isPostHogReady(): boolean {
        return !!(window.posthog && typeof window.posthog.capture === 'function');
    }

    private isMixpanelReady(): boolean {
        return !!(window.mixpanel && typeof window.mixpanel.track === 'function');
    }

    private isGTMReady(): boolean {
        return Array.isArray(window.dataLayer);
    }

    /**
     * GA4 dataLayer push (GTM을 통한 이벤트 전송)
     */
    private pushToDataLayer(event: string, properties?: EventProperties) {
        if (!this.isGTMReady()) return;
        
        // GA4 이벤트명은 snake_case로 변환 (Title Case -> snake_case)
        const ga4EventName = event.toLowerCase().replace(/ /g, '_');
        
        window.dataLayer!.push({
            event: ga4EventName,
            ...properties
        });
        
        if (this.debugMode) console.log('[GA4/GTM] Push:', ga4EventName, properties);
    }

    /**
     * 사용자 식별 + User Properties 설정
     */
    identify(userId: string, properties?: Partial<UserProperties>) {
        const userProps: Partial<UserProperties> = {
            user_id: userId,
            user_type: properties?.user_type || 'free',
            signup_cohort_date: properties?.signup_date ? properties.signup_date.split('T')[0] : undefined,
            experience_level: this.calculateExperienceLevel(properties?.current_xp || 0),
            total_problems_solved: properties?.total_problems_solved || 0,
            ...properties
        };

        if (this.isMixpanelReady()) {
            window.mixpanel!.identify(userId);
            window.mixpanel!.people.set(userProps);
            if (this.debugMode) console.log('[Mixpanel] Identified:', userId, userProps);
        }

        if (this.isPostHogReady()) {
            window.posthog!.identify(userId, userProps);
            if (this.debugMode) console.log('[PostHog] Identified:', userId);
        }

        // GA4: GTM을 통해 사용자 ID 설정
        if (this.isGTMReady()) {
            window.dataLayer!.push({
                event: 'user_identified',
                user_id: userId,
                user_properties: userProps
            });
            if (this.debugMode) console.log('[GA4/GTM] User Identified:', userId);
        }
    }

    private calculateExperienceLevel(xp: number): string {
        if (xp >= 1000) return '고수';
        if (xp >= 300) return '중수';
        return '초보';
    }

    /**
     * 사용자 식별 해제 (로그아웃)
     */
    reset() {
        if (this.isMixpanelReady()) {
            window.mixpanel!.reset();
            if (this.debugMode) console.log('[Mixpanel] Reset');
        }

        if (this.isPostHogReady()) {
            window.posthog!.reset();
            if (this.debugMode) console.log('[PostHog] Reset');
        }
    }

    /**
     * 이벤트 추적 - 핵심 메서드
     */
    track(event: AnalyticsEvent | string, properties?: EventProperties) {
        const eventData: EventProperties = {
            ...properties,
            timestamp: new Date().toISOString(),
            page: window.location.pathname,
            env: this.env
        };

        if (this.isMixpanelReady()) {
            try {
                window.mixpanel!.track(event, eventData);
                if (this.debugMode) console.log('[Mixpanel] Track:', event, eventData);
            } catch (e) {
                if (this.debugMode) console.warn('[Mixpanel] Track failed:', e);
            }
        }

        if (this.isPostHogReady()) {
            try {
                window.posthog!.capture(event, eventData);
                if (this.debugMode) console.log('[PostHog] Capture:', event, eventData);
            } catch (e) {
                if (this.debugMode) console.warn('[PostHog] Capture failed:', e);
            }
        }

        // GA4: GTM dataLayer를 통한 이벤트 전송
        this.pushToDataLayer(event, eventData);
    }

    // ============ 내부 카운터 관리 ============

    private getAttemptCount(problemId: string): number {
        return this.attemptCounts[problemId] || 0;
    }

    private incrementAttempt(problemId: string): number {
        this.attemptCounts[problemId] = (this.attemptCounts[problemId] || 0) + 1;
        return this.attemptCounts[problemId];
    }

    private incrementExecution(problemId: string): number {
        this.executionCounts[problemId] = (this.executionCounts[problemId] || 0) + 1;
        return this.executionCounts[problemId];
    }

    private getProblemTimeSpent(): number {
        return Math.floor((Date.now() - this.startTime) / 1000);
    }

    private resetProblemTimer() {
        this.startTime = Date.now();
    }

    // ============ 편의 메서드 (Tracking Plan 준수) ============

    pageView(pageName: string, properties?: EventProperties) {
        this.track('Page Viewed', { ...properties, page: pageName });
    }

    signUpCompleted(userId: string, provider: 'google' | 'kakao' | 'email') {
        this.track('Sign Up Completed', { user_id: userId, auth_provider: provider, is_new_user: true });
    }

    loginSuccess(userId: string, provider: 'google' | 'kakao' | 'email') {
        this.track('Login Success', { user_id: userId, auth_provider: provider });
    }

    logoutCompleted() {
        this.track('Logout Completed', {});
        this.reset();
    }

    /** 1) Problem Viewed */
    problemViewed(problemId: string, metadata: { difficulty: any, dataType: string, isDaily?: boolean, topic?: string }) {
        this.resetProblemTimer(); // 진입 시 타이머 리셋
        this.track('Problem Viewed', {
            problem_id: problemId,
            difficulty_level: metadata.difficulty,
            data_type: metadata.dataType,
            is_daily_problem: metadata.isDaily,
            topic_tags: metadata.topic
        });
    }

    /** 2) Problem Attempted (첫 타이핑/실행) */
    problemAttempted(problemId: string, difficulty: any) {
        // 이미 해당 세션에서 시도했다면 무시 (최초 1회만)
        if (this.getAttemptCount(problemId) === 0) {
            this.incrementAttempt(problemId);
            this.track('Problem Attempted', {
                problem_id: problemId,
                difficulty_level: difficulty,
                attempt_count: 1
            });
        }
    }

    /** 3) SQL Executed & Error */
    sqlExecuted(problemId: string, details: { sql: string, hasError: boolean, errorType?: string, errorMessage?: string, dbEngine?: string }) {
        const count = this.incrementExecution(problemId);
        this.track('SQL Executed', {
            problem_id: problemId,
            sql_text: details.sql,
            sql_length: details.sql.length,
            execution_count: count,
            db_engine: details.dbEngine || 'postgres'
        });

        if (details.hasError) {
            this.track('SQL Error Occurred', {
                problem_id: problemId,
                error_type: details.errorType || 'runtime',
                error_message: details.errorMessage,
                sql_text: details.sql
            });
        }
    }

    /** 4) Problem Submitted & Solved/Failed */
    problemSubmitted(problemId: string, result: { isCorrect: boolean, difficulty: any, dataType: string }) {
        const count = this.getAttemptCount(problemId) || 1; // Attempted 이벤트를 안거쳤을 수도 있으니 최소 1
        const timeSpent = this.getProblemTimeSpent();

        this.track('Problem Submitted', {
            problem_id: problemId,
            difficulty_level: result.difficulty,
            attempt_count: count,
            result: result.isCorrect ? 'success' : 'fail',
            data_type: result.dataType
        });

        if (result.isCorrect) {
            this.track('Problem Solved', {
                problem_id: problemId,
                difficulty_level: result.difficulty,
                attempt_count: count,
                time_spent_sec: timeSpent,
                data_type: result.dataType
            });
            // 유저 프로필 업데이트
            if (this.isMixpanelReady()) {
                window.mixpanel!.people.increment('total_problems_solved', 1);
            }
        } else {
            this.track('Problem Failed', {
                problem_id: problemId,
                difficulty_level: result.difficulty,
                attempt_count: count,
                data_type: result.dataType
            });
        }

        // 제출할 때마다 시도 횟수 증가 (다음 제출을 위해)
        this.incrementAttempt(problemId);
    }

    /** Hint Requested */
    hintRequested(problemId: string, difficulty: any, dataType: string) {
        this.track('Hint Requested', {
            problem_id: problemId,
            difficulty_level: difficulty,
            data_type: dataType
        });
    }

    tabChanged(tab: string, dataType: string) {
        this.track('Tab Changed', { tab_name: tab, data_type: dataType });
    }

    schemaViewed(dataType: string) {
        this.track('Schema Viewed', { data_type: dataType });
    }
}

// 싱글톤 인스턴스
export const analytics = new Analytics();

// SDK 초기화 함수
export function initAnalytics() {
    console.log('[Analytics] Init check - Mixpanel:', !!window.mixpanel, 'PostHog:', !!window.posthog);
    console.log('[Analytics] Environment:', getEnvironment());

    // Mixpanel 초기화
    const mixpanelToken = (import.meta.env.VITE_MIXPANEL_TOKEN as string) || '';
    if (mixpanelToken && window.mixpanel && typeof window.mixpanel.init === 'function') {
        window.mixpanel.init(mixpanelToken, {
            autocapture: true,
            record_sessions_percent: 100,
        });
        console.log('[Analytics] Mixpanel Initialized with token');
    }
}
