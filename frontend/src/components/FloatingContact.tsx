// frontend/src/components/FloatingContact.tsx
import { useState } from 'react';
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

    const hasLinks = Object.values(CONTACT_LINKS).some(url => url);

    const handleClick = (url: string) => {
        if (url) {
            window.open(url, '_blank');
        }
    };

    return (
        <div className="floating-contact">
            <button
                className={`floating-btn ${isOpen ? 'open' : ''}`}
                onClick={() => setIsOpen(!isOpen)}
                aria-label="연락처 메뉴"
            >
                {isOpen ? '✕' : '💬'}
            </button>

            {isOpen && (
                <div className="floating-menu">
                    <div className="floating-menu-header">
                        문의하기
                    </div>

                    {CONTACT_LINKS.kakao && (
                        <button
                            className="floating-menu-item kakao"
                            onClick={() => handleClick(CONTACT_LINKS.kakao)}
                        >
                            <span className="icon">💬</span>
                            <span>카카오톡 채널</span>
                        </button>
                    )}

                    {CONTACT_LINKS.slack && (
                        <button
                            className="floating-menu-item slack"
                            onClick={() => handleClick(CONTACT_LINKS.slack)}
                        >
                            <span className="icon">💼</span>
                            <span>Slack 참여</span>
                        </button>
                    )}

                    {CONTACT_LINKS.faq && (
                        <button
                            className="floating-menu-item faq"
                            onClick={() => handleClick(CONTACT_LINKS.faq)}
                        >
                            <span className="icon">❓</span>
                            <span>FAQ</span>
                        </button>
                    )}

                    {CONTACT_LINKS.email && (
                        <button
                            className="floating-menu-item email"
                            onClick={() => handleClick(`mailto:${CONTACT_LINKS.email}`)}
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
