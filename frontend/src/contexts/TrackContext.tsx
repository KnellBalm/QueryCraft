import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';

// Track 타입 정의
export type Track = 'core' | 'future';

// 컨텍스트 타입
interface TrackContextType {
    track: Track;
    setTrack: (track: Track) => void;
    isCore: boolean;
    isFuture: boolean;
}

// 컨텍스트 생성
const TrackContext = createContext<TrackContextType | undefined>(undefined);

// 로컬스토리지 키
const TRACK_STORAGE_KEY = 'querycraft_track';

// Provider 컴포넌트
interface TrackProviderProps {
    children: ReactNode;
}

export function TrackProvider({ children }: TrackProviderProps) {
    // 로컬스토리지에서 초기값 로드 (기본값: core)
    const [track, setTrackState] = useState<Track>(() => {
        const saved = localStorage.getItem(TRACK_STORAGE_KEY);
        return (saved === 'core' || saved === 'future') ? saved : 'core';
    });

    // 트랙 변경 시 로컬스토리지 저장 및 data-track 속성 업데이트
    const setTrack = (newTrack: Track) => {
        setTrackState(newTrack);
        localStorage.setItem(TRACK_STORAGE_KEY, newTrack);
    };

    // data-track 속성을 document.documentElement에 적용
    useEffect(() => {
        document.documentElement.setAttribute('data-track', track);
    }, [track]);

    const value: TrackContextType = {
        track,
        setTrack,
        isCore: track === 'core',
        isFuture: track === 'future',
    };

    return (
        <TrackContext.Provider value={value}>
            {children}
        </TrackContext.Provider>
    );
}

// 커스텀 훅
export function useTrack(): TrackContextType {
    const context = useContext(TrackContext);
    if (context === undefined) {
        throw new Error('useTrack must be used within a TrackProvider');
    }
    return context;
}

export default TrackContext;
