// frontend/src/services/analytics.ts
/**
 * 이벤트 트래킹 서비스
 * Mixpanel (CDN) 또는 PostHog (React SDK) 연동
 */

// Mixpanel 전역 타입 선언
declare global {
    interface Window {
        mixpanel?: {
            init: (token: string, config?: object) => void;
            track: (event: string, properties?: object) => void;
            identify: (userId: string) => void;
            reset: () => void;
            people: {
                set: (properties: object) => void;
            };
        };
        posthog?: {
            init: (key: string, config?: object) => void;
            capture: (event: string, properties?: object) => void;
            identify: (userId: string, properties?: object) => void;
            reset: () => void;
        };
    }
}

// 이벤트 타입 정의
export type AnalyticsEvent =
    | 'page_view'
    | 'page_leave'
    | 'problem_view'
    | 'problem_attempt'
    | 'problem_submit'
    | 'problem_correct'
    | 'problem_incorrect'
    | 'problem_hint_request'
    | 'sql_execute'
    | 'sql_error'
    | 'user_login'
    | 'user_logout'
    | 'user_signup'
    | 'tab_change'
    | 'contact_button_click'
    | 'schema_view';

// 이벤트 속성 타입
export interface EventProperties {
    timestamp?: string;
    page?: string;
    problem_id?: string;
    problem_difficulty?: string;
    problem_topic?: string;
    data_type?: 'pa' | 'stream';
    is_correct?: boolean;
    attempt_number?: number;
    time_spent_seconds?: number;
    sql_length?: number;
    error_message?: string;
    auth_provider?: 'google' | 'kakao';
    has_error?: boolean;
    [key: string]: unknown;
}


class Analytics {
    /**
     * PostHog가 제대로 초기화되었는지 확인
     */
    private isPostHogReady(): boolean {
        return !!(window.posthog && typeof window.posthog.capture === 'function');
    }

    /**
     * Mixpanel이 제대로 초기화되었는지 확인
     */
    private isMixpanelReady(): boolean {
        return !!(window.mixpanel && typeof window.mixpanel.track === 'function');
    }

    /**
     * 사용자 식별
     */
    identify(userId: string, traits?: Record<string, unknown>) {
        if (this.isMixpanelReady()) {
            window.mixpanel!.identify(userId);
            if (traits) {
                window.mixpanel!.people.set(traits);
            }
            console.log('[Mixpanel] Identified:', userId);
        }

        if (this.isPostHogReady()) {
            window.posthog!.identify(userId, traits);
            console.log('[PostHog] Identified:', userId);
        }
    }

    /**
     * 사용자 식별 해제 (로그아웃)
     */
    reset() {
        if (this.isMixpanelReady()) {
            window.mixpanel!.reset();
            console.log('[Mixpanel] Reset');
        }

        if (this.isPostHogReady()) {
            window.posthog!.reset();
            console.log('[PostHog] Reset');
        }
    }

    /**
     * 이벤트 추적 - 핵심 메서드
     */
    track(event: AnalyticsEvent | string, properties?: EventProperties) {
        const eventData = {
            ...properties,
            timestamp: new Date().toISOString(),
            page: window.location.pathname
        };

        // Mixpanel
        if (this.isMixpanelReady()) {
            try {
                window.mixpanel!.track(event, eventData);
                console.log('[Mixpanel] Track:', event, eventData);
            } catch (e) {
                console.warn('[Mixpanel] Track failed:', e);
            }
        }

        // PostHog
        if (this.isPostHogReady()) {
            try {
                window.posthog!.capture(event, eventData);
                console.log('[PostHog] Capture:', event, eventData);
            } catch (e) {
                console.warn('[PostHog] Capture failed:', e);
            }
        }
    }

    /**
     * 페이지뷰 추적
     */
    pageView(pageName: string, properties?: EventProperties) {
        this.track('page_view', { ...properties, page: pageName });
    }

    /**
     * 문제 풀이 시작
     */
    problemStart(problemId: string, difficulty: string, topic: string, dataType: 'pa' | 'stream') {
        this.track('problem_view', {
            problem_id: problemId,
            problem_difficulty: difficulty,
            problem_topic: topic,
            data_type: dataType
        });
    }

    /**
     * 문제 제출
     */
    problemSubmit(problemId: string, isCorrect: boolean, attemptNumber: number, timeSpent: number) {
        this.track('problem_submit', {
            problem_id: problemId,
            is_correct: isCorrect,
            attempt_number: attemptNumber,
            time_spent_seconds: timeSpent
        });

        // 정답/오답 별도 이벤트
        this.track(isCorrect ? 'problem_correct' : 'problem_incorrect', {
            problem_id: problemId,
            attempt_number: attemptNumber
        });
    }

    /**
     * SQL 실행
     */
    sqlExecute(sqlLength: number, hasError: boolean, errorMessage?: string) {
        this.track('sql_execute', {
            sql_length: sqlLength,
            has_error: hasError,
            error_message: errorMessage
        });

        if (hasError && errorMessage) {
            this.track('sql_error', { error_message: errorMessage });
        }
    }

    /**
     * 힌트 요청
     */
    hintRequest(problemId: string, difficulty: string, dataType: 'pa' | 'stream') {
        this.track('problem_hint_request', {
            problem_id: problemId,
            problem_difficulty: difficulty,
            data_type: dataType
        });
    }

    /**
     * 탭 변경
     */
    tabChange(tab: string, dataType: 'pa' | 'stream') {
        this.track('tab_change', { tab, data_type: dataType });
    }

    /**
     * 로그인 이벤트
     */
    login(provider: 'google' | 'kakao') {
        this.track('user_login', { auth_provider: provider });
    }

    /**
     * 로그아웃 이벤트
     */
    logout() {
        this.track('user_logout', {});
        this.reset();
    }

    /**
     * 스키마 조회
     */
    schemaView(dataType: 'pa' | 'stream') {
        this.track('schema_view', { data_type: dataType });
    }

    /**
     * 연락 버튼 클릭
     */
    contactClick() {
        this.track('contact_button_click', {});
    }
}

// 싱글톤 인스턴스
export const analytics = new Analytics();

// SDK 초기화 함수 (이미 index.html에서 로드되므로 보통 필요 없음)
export function initAnalytics() {
    console.log('[Analytics] Init check - Mixpanel:', !!window.mixpanel, 'PostHog:', !!window.posthog);
}
