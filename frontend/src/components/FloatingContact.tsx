// frontend/src/components/FloatingContact.tsx
import { useState, useEffect, useRef } from 'react';
import './FloatingContact.css';

// URL은 환경변수 또는 설정에서 관리 (나중에 수정 가능)
const CONTACT_LINKS = {
    kakao: '', // 카카오톡 채널 URL
    slack: '', // Slack 초대 링크
    faq: '',   // FAQ 페이지 URL
    email: '', // 이메일 주소
};

export function FloatingContact() {
    const [isOpen, setIsOpen] = useState(false);
    const containerRef = useRef<HTMLDivElement>(null);

    const hasLinks = Object.values(CONTACT_LINKS).some(url => url);

    const handleClick = (url: string) => {
        if (url) {
            window.open(url, '_blank');
        }
    };

    // 메뉴가 열려있을 때 외부 클릭 및 ESC 키 처리
    useEffect(() => {
        const handleKeyDown = (event: KeyboardEvent) => {
            if (event.key === 'Escape') {
                setIsOpen(false);
            }
        };

        const handleClickOutside = (event: MouseEvent) => {
            if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        };

        if (isOpen) {
            document.addEventListener('keydown', handleKeyDown);
            document.addEventListener('mousedown', handleClickOutside);
        }

        return () => {
            document.removeEventListener('keydown', handleKeyDown);
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, [isOpen]);

    return (
        <div className="floating-contact" ref={containerRef}>
            <button
                className={`floating-btn ${isOpen ? 'open' : ''}`}
                onClick={() => setIsOpen(!isOpen)}
                aria-label="연락처 메뉴"
                aria-haspopup="true"
                aria-expanded={isOpen}
                aria-controls="floating-menu"
            >
                {isOpen ? '✕' : '💬'}
            </button>

            {isOpen && (
                <div
                    id="floating-menu"
                    className="floating-menu"
                    role="menu"
                >
                    <div className="floating-menu-header">
                        문의하기
                    </div>

                    {CONTACT_LINKS.kakao && (
                        <button
                            className="floating-menu-item kakao"
                            onClick={() => handleClick(CONTACT_LINKS.kakao)}
                            role="menuitem"
                        >
                            <span className="icon">💬</span>
                            <span>카카오톡 채널</span>
                        </button>
                    )}

                    {CONTACT_LINKS.slack && (
                        <button
                            className="floating-menu-item slack"
                            onClick={() => handleClick(CONTACT_LINKS.slack)}
                            role="menuitem"
                        >
                            <span className="icon">💼</span>
                            <span>Slack 참여</span>
                        </button>
                    )}

                    {CONTACT_LINKS.faq && (
                        <button
                            className="floating-menu-item faq"
                            onClick={() => handleClick(CONTACT_LINKS.faq)}
                            role="menuitem"
                        >
                            <span className="icon">❓</span>
                            <span>FAQ</span>
                        </button>
                    )}

                    {CONTACT_LINKS.email && (
                        <button
                            className="floating-menu-item email"
                            onClick={() => handleClick(`mailto:${CONTACT_LINKS.email}`)}
                            role="menuitem"
                        >
                            <span className="icon">✉️</span>
                            <span>이메일 문의</span>
                        </button>
                    )}

                    {!hasLinks && (
                        <div className="floating-menu-empty">
                            <span className="icon">🔧</span>
                            <span>링크 설정 중...</span>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
