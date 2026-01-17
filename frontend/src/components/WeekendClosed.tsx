import React from 'react';
import { Link } from 'react-router-dom';
import './WeekendClosed.css';

const WeekendClosed: React.FC = () => {
    return (
        <div className="weekend-closed-container">
            <div className="weekend-closed-content">
                <div className="weekend-closed-icon">😴</div>
                <h1>주말에는 QueryCraft도 쉽니다</h1>
                <p>QueryCraft는 평일(월~금)에만 운영됩니다.</p>
                <p>재충전 후 월요일에 더 좋은 문제로 찾아뵙겠습니다!</p>
                <div className="weekend-closed-info">
                    <span>운영 시간: 월요일 09:00 ~ 토요일 01:00</span>
                </div>
                <div className="weekend-practice-link">
                    <Link to="/practice" className="practice-link-btn">
                        ♾️ 연습 모드는 주말에도 이용 가능해요!
                    </Link>
                </div>
            </div>
        </div>
    );
};

export default WeekendClosed;
