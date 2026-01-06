// frontend/src/components/Onboarding.tsx
/**
 * 온보딩 튜토리얼 - 페이지 이동 + 하이라이팅
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { analytics } from '../services/analytics';
import './Onboarding.css';

// localStorage 키
const ONBOARDING_KEY = 'sql_labs_onboarding_completed';

// 외부에서 호출 가능한 온보딩 리셋 함수
let resetOnboardingCallback: (() => void) | null = null;

export function resetOnboarding() {
    localStorage.removeItem(ONBOARDING_KEY);
    if (resetOnboardingCallback) {
        resetOnboardingCallback();
    }
}

interface OnboardingStep {
    id: string;
    page: string;
    target: string;
    title: string;
    content: string;
    placement: 'top' | 'bottom' | 'left' | 'right' | 'center';
}

const onboardingSteps: OnboardingStep[] = [

    // 메인페이지 (3단계)
    {
        id: 'welcome',
        page: '/',
        target: 'body',
        title: '🎉 환영합니다!',
        content: 'SQL 트레이닝 센터에 오신 것을 환영합니다.\n간단한 튜토리얼을 시작합니다!',
        placement: 'center',
    },
    {
        id: 'nav-menu',
        page: '/',
        target: '.nav',
        title: '🧭 네비게이션',
        content: 'PA 연습, 스트림 연습, 무한 연습 중 원하는 학습 모드를 선택하세요.',
        placement: 'bottom',
    },
    {
        id: 'user-stats',
        page: '/',
        target: '.user-stats',
        title: '📊 나의 현황',
        content: '연속 출석일, 레벨, 정답 수 등 학습 현황을 확인할 수 있어요.',
        placement: 'bottom',
    },
    // PA 연습 페이지 (7단계)
    {
        id: 'pa-intro',
        page: '/pa',
        target: 'body',
        title: '📈 PA 연습 모드',
        content: '이커머스, 핀테크 등 실무 데이터 분석 문제를 풀어보세요!',
        placement: 'center',
    },
    {
        id: 'problem-list',
        page: '/pa',
        target: '.problem-list',
        title: '📋 문제 목록',
        content: '🟢 Easy, 🟡 Medium, 🔴 Hard\n풀고 싶은 문제를 클릭하세요!',
        placement: 'right',
    },
    {
        id: 'problem-detail',
        page: '/pa',
        target: '.problem-detail',
        title: '📝 문제 상세',
        content: '선택한 문제의 요청사항과 컨텍스트를 확인하세요.\n필요한 컬럼과 조건을 파악하는 것이 중요해요!',
        placement: 'left',
    },
    {
        id: 'tab-schema',
        page: '/pa',
        target: '.panel-tabs',
        title: '📋 스키마 탭',
        content: '"스키마" 탭을 클릭하면 테이블과 컬럼 정보를 볼 수 있어요.',
        placement: 'bottom',
    },
    {
        id: 'editor',
        page: '/pa',
        target: '.editor-shell',
        title: '⌨️ SQL 에디터',
        content: 'SQL 쿼리를 작성하세요.\nCtrl+Enter로 실행할 수 있어요!',
        placement: 'top',
    },
    {
        id: 'buttons',
        page: '/pa',
        target: '.editor-actions',
        title: '🎮 실행과 제출',
        content: '▶️ 실행: 결과만 확인\n✅ 제출: 정답과 비교하여 채점',
        placement: 'top',
    },
    {
        id: 'result',
        page: '/pa',
        target: '.result-section',
        title: '📊 결과 확인',
        content: '쿼리 실행 결과와 채점 피드백이 여기에 표시됩니다.',
        placement: 'top',
    },
    {
        id: 'complete',
        page: '/pa',
        target: 'body',
        title: '🚀 준비 완료!',
        content: '이제 직접 문제를 풀어보세요!\n매일 풀면 레벨업! 화이팅! 💪',
        placement: 'center',
    },
];

export function Onboarding() {
    const { user } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();

    const [isActive, setIsActive] = useState(false);
    const [currentStep, setCurrentStep] = useState(0);
    const [isNavigating, setIsNavigating] = useState(false);
    const [tooltipStyle, setTooltipStyle] = useState<React.CSSProperties>({});
    const highlightRef = useRef<HTMLDivElement>(null);
    const updateRef = useRef<number>(0);

    const step = onboardingSteps[currentStep];

    // 외부에서 온보딩 리셋 가능하도록 콜백 등록
    useEffect(() => {
        resetOnboardingCallback = () => {
            setCurrentStep(0);
            setIsActive(true);
        };
        return () => {
            resetOnboardingCallback = null;
        };
    }, []);

    // 툴팁 위치 계산
    const updatePosition = useCallback(() => {
        if (!step) return;

        const currentUpdate = ++updateRef.current;

        // 중앙 배치
        if (step.placement === 'center' || step.target === 'body') {
            setTooltipStyle({
                position: 'fixed',
                top: '50%',
                left: '50%',
                transform: 'translate(-50%, -50%)',
            });
            if (highlightRef.current) {
                highlightRef.current.style.display = 'none';
            }
            setIsNavigating(false);
            return;
        }

        // 요소 찾기 (즉시 + 폴링)
        const findAndPosition = () => {
            if (currentUpdate !== updateRef.current) return; // 취소됨

            const el = document.querySelector(step.target);
            if (!el) {
                // 100ms 후 재시도 (최대 2초)
                setTimeout(findAndPosition, 100);
                return;
            }

            const rect = el.getBoundingClientRect();
            const padding = 8;

            // 하이라이트 박스
            if (highlightRef.current) {
                highlightRef.current.style.display = 'block';
                highlightRef.current.style.top = `${rect.top - padding}px`;
                highlightRef.current.style.left = `${rect.left - padding}px`;
                highlightRef.current.style.width = `${rect.width + padding * 2}px`;
                highlightRef.current.style.height = `${rect.height + padding * 2}px`;
            }

            // 툴팁 위치
            let top = 0, left = 0;
            const tooltipWidth = 340;
            const tooltipHeight = 140;

            switch (step.placement) {
                case 'top':
                    top = rect.top - tooltipHeight - 20;
                    left = rect.left + rect.width / 2 - tooltipWidth / 2;
                    break;
                case 'bottom':
                    top = rect.bottom + 20;
                    left = rect.left + rect.width / 2 - tooltipWidth / 2;
                    break;
                case 'left':
                    top = rect.top + rect.height / 2 - tooltipHeight / 2;
                    left = rect.left - tooltipWidth - 20;
                    break;
                case 'right':
                    top = rect.top + rect.height / 2 - tooltipHeight / 2;
                    left = rect.right + 20;
                    break;
            }

            // 화면 범위 조정
            top = Math.max(10, Math.min(top, window.innerHeight - tooltipHeight - 10));
            left = Math.max(10, Math.min(left, window.innerWidth - tooltipWidth - 10));

            setTooltipStyle({
                position: 'fixed',
                top: `${top}px`,
                left: `${left}px`,
            });
            setIsNavigating(false);
        };

        findAndPosition();
    }, [step]);

    // 온보딩 시작
    useEffect(() => {
        const hasCompleted = localStorage.getItem(ONBOARDING_KEY) === 'true';

        // 이미 완료한 경우 표시 안함
        if (hasCompleted) {
            return;
        }

        if (location.pathname === '/') {
            const timer = setTimeout(() => {
                setIsActive(true);
                setCurrentStep(0);
                analytics.track('Onboarding Started', { user_id: user?.id || 'guest' });
            }, 800);
            return () => clearTimeout(timer);
        }
    }, [user, location.pathname]);

    // 페이지 이동 처리
    useEffect(() => {
        if (!isActive || !step) return;

        if (step.page !== location.pathname) {
            setIsNavigating(true);
            navigate(step.page);
        } else {
            // 같은 페이지면 바로 위치 업데이트
            updatePosition();
        }
    }, [isActive, currentStep, step, location.pathname, navigate, updatePosition]);

    // 페이지 로드 후 위치 업데이트
    useEffect(() => {
        if (!isActive || !step) return;

        if (step.page === location.pathname) {
            // 짧은 딜레이 후 위치 계산
            const timer = setTimeout(updatePosition, 150);
            return () => clearTimeout(timer);
        }
    }, [isActive, step, location.pathname, updatePosition]);

    // 리사이즈/스크롤 대응
    useEffect(() => {
        if (!isActive) return;

        const handleUpdate = () => updatePosition();
        window.addEventListener('resize', handleUpdate);
        window.addEventListener('scroll', handleUpdate, true);

        return () => {
            window.removeEventListener('resize', handleUpdate);
            window.removeEventListener('scroll', handleUpdate, true);
        };
    }, [isActive, updatePosition]);

    const handleNext = () => {
        if (currentStep < onboardingSteps.length - 1) {
            setIsNavigating(true);
            setCurrentStep(currentStep + 1);
        } else {
            handleComplete();
        }
    };

    const handlePrev = () => {
        if (currentStep > 0) {
            setIsNavigating(true);
            setCurrentStep(currentStep - 1);
        }
    };

    const handleSkip = () => {
        localStorage.setItem(ONBOARDING_KEY, 'true');
        analytics.track('Onboarding Skipped', { step: currentStep + 1, user_id: user?.id || 'guest' });
        setIsActive(false);
    };

    const handleComplete = () => {
        localStorage.setItem(ONBOARDING_KEY, 'true');
        analytics.track('Onboarding Completed', { user_id: user?.id || 'guest' });
        setIsActive(false);
    };

    if (!isActive || !step) return null;

    const isLast = currentStep === onboardingSteps.length - 1;

    return (
        <div className="onboarding-overlay">
            {/* 하이라이트 박스 */}
            <div ref={highlightRef} className="onboarding-highlight-box" />

            {/* 툴팁 */}
            <div className="onboarding-tooltip" style={tooltipStyle}>
                {isNavigating ? (
                    <div className="onboarding-loading">⏳ 로딩 중...</div>
                ) : (
                    <>
                        <div className="onboarding-header">
                            <span className="step-indicator">{currentStep + 1} / {onboardingSteps.length}</span>
                        </div>
                        <h3 className="onboarding-title">{step.title}</h3>
                        <p className="onboarding-content">
                            {step.content.split('\n').map((line, i) => <span key={i}>{line}<br /></span>)}
                        </p>
                        <div className="onboarding-buttons">
                            <button className="btn-skip" onClick={handleSkip}>건너뛰기</button>
                            <div className="btn-group">
                                {currentStep > 0 && (
                                    <button className="btn-prev" onClick={handlePrev}>이전</button>
                                )}
                                <button className="btn-next" onClick={handleNext}>
                                    {isLast ? '시작하기' : '다음'}
                                </button>
                            </div>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
}
