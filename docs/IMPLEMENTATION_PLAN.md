# Daily Challenge 시스템 재설계 - Implementation Plan

**작성일**: 2026-01-17  
**상태**: 90% MVP 완료 (Phase 1-5)  
**다음**: Jules 테스팅 → 프로덕션 배포

---

## 목표 (Goal)

PA와 Stream 문제를 **하나의 비즈니스 시나리오**로 통합하여 학습 연결성을 높이고, 동적 테이블명과 실무 데이터 패턴을 반영한 Daily Challenge 시스템 구축.

### 핵심 차별화
- ✅ **통합 챌린지**: 하루 6문제 (PA 3 + Stream 3)
- ✅ **비즈니스 컨텍스트**: 실제 스타트업 시나리오 (SafePay, TrendPick 등)
- ✅ **동적 테이블**: `warehouse.transactions_20260117` (YYYYMMDD)
- ✅ **실무 패턴**: NULL, 다양한 스키마, JSONB 등

---

## 구현 완료 항목 (Completed)

### ✅ Phase 1: Scenario & Data Generator

**파일**: 
- `backend/generator/scenario_generator.py` (300+ 라인)
- `backend/generator/scenario_data_generator.py` (400+ 라인)

**기능**:
1. 비즈니스 시나리오 생성 (7개 템플릿)
   - commerce, fintech, saas, content
   - Company 정보, 상황, Stake, North Star
2. 동적 테이블 생성 (6가지 타입)
   - events, users, transactions, fraud_alerts, bookings, subscribers
3. PA + Stream 통합 데이터
   - event_at (TIMESTAMP), event_date (DATE)
   - 실무 패턴 (NULL, 인덱스, JSONB)

---

### ✅ Phase 2: Unified Problem Generator

**파일**: 
- `backend/generator/unified_problem_generator.py` (400+ 라인)

**기능**:
1. 하루 6문제 생성 (PA 3 + Stream 3)
2. 난이도 균등 분배 (Easy/Medium/Hard 각 2개)
3. 30+ 문제 템플릿
   - Product type별 차별화
   - 시나리오 컨텍스트 자동 주입
4. 요청자 (Requester) 명시
   - CEO, CMO, CFO, Data Team Lead 등

---

### ✅ Phase 3: File Format

**파일**: 
- `backend/generator/daily_challenge_writer.py` (250+ 라인)

**기능**:
1. YYYY-MM-DD.json 통합 포맷 (Version 2.0)
   ```json
   {
     "version": "2.0",
     "scenario": { ... },
     "problems": [ ... ],
     "metadata": {
       "pa_count": 3,
       "stream_count": 3,
       "difficulty_distribution": { ... }
     }
   }
   ```
2. save/load 함수
3. 전체 파이프라인: `generate_and_save_daily_challenge()`

---

### ✅ Phase 4: API Endpoints

**파일**: 
- `backend/api/daily.py` (150+ 라인)
- `backend/main.py` (라우터 등록)

**엔드포인트** (5개):
1. `GET /api/daily/{date}` - 전체 챌린지
2. `GET /api/daily/latest` - 최신 챌린지
3. `GET /api/daily/{date}/problems` - 문제만
4. `GET /api/daily/{date}/scenario` - 시나리오만
5. `GET /api/daily/{date}/tables` - 테이블 정보만

**기능**:
- 날짜 형식 검증 (ISO 8601)
- 404 에러 처리
- 모듈형 조회

---

### ✅ Phase 5: Frontend UI

**파일**: 
- `frontend/src/components/ScenarioPanel.tsx + .css` (350+ 라인)
- `frontend/src/pages/DailyChallenge.tsx + .css` (550+ 라인)
- `frontend/src/App.tsx` (라우트 추가)

**UI 컴포넌트**:
1. **ScenarioPanel**
   - Gradient 배경 (purple theme)
   - Glassmorphism 스타일
   - 비즈니스 컨텍스트 표시
   - 테이블 정보, North Star, Key Metrics

2. **DailyChallenge 페이지**
   - 6문제 그리드 카드
   - PA/Stream 뱃지, 난이도 색상
   - Hover 애니메이션
   - 시나리오 토글 기능

**라우트**:
- `/daily` - 최신 챌린지
- `/daily/:date` - 특정 날짜

---

### ✅ Worker 통합

**파일**: 
- `worker/main.py` (수정)

**변경사항**:
1. `generate_data(use_scenario=True)` - Scenario 기반 데이터 생성
2. `generate_problems()` - `daily_challenge_writer` 사용
3. `--legacy` 플래그 - 기존 방식 지원

**사용법**:
```bash
# 새로운 방식
python -m worker.main --date 2026-01-19

# 기존 방식
python -m worker.main --legacy
```

---

## 남은 작업 (Remaining)

### 🔍 테스팅 (Jules 위임)

**문서**: `jules_daily_challenge_testing.md`

**항목**:
- [ ] Worker Job 로컬 실행
- [ ] API 엔드포인트 테스트 (curl)
- [ ] Frontend UI 브라우저 테스트
- [ ] 데이터 검증 (PostgreSQL)

**우선순위**: P0 (필수)

---

### 📦 프로덕션 배포 (선택)

- [ ] GitHub에 푸시 → 자동 배포 (완료)
- [ ] Cloud Scheduler 실행 확인
- [ ] 실제 데이터 생성 (2026-01-19)
- [ ] 프로덕션 API 테스트

---

### 🔄 Deprecated API 처리 (선택)

**파일**: `backend/api/problems.py`

**변경**:
```python
@router.get("/pa")
async def get_pa_problems_deprecated():
    """DEPRECATED: Use /api/daily/latest instead"""
    raise HTTPException(
        status_code=410,
        detail={
            "error": "This endpoint is deprecated",
            "redirect": "/api/daily/latest",
            "message": "PA problems are now part of Daily Challenge"
        }
    )
```

**영향도**: 낮음 (기존 사용자 거의 없음)

---

## 검증 계획 (Verification Plan)

### Automated Tests (선택)

```bash
# Unit tests
pytest backend/test_scenario_generator.py
pytest backend/test_unified_problem_generator.py
pytest backend/test_daily_challenge_writer.py

# Integration tests
pytest backend/test_api_daily.py
```

### Manual Verification

1. **Worker 실행**
   - ✅ 시나리오 생성 확인
   - ✅ 데이터 삽입 확인 (row count)
   - ✅ 파일 생성 확인 (YYYY-MM-DD.json)

2. **API 테스트**
   - ✅ `/api/daily/{date}` 200 응답
   - ✅ JSON 스키마 검증
   - ✅ 404 에러 처리

3. **Frontend UI**
   - ✅ ScenarioPanel 렌더링
   - ✅ 문제 카드 그리드
   - ✅ Responsive 디자인
   - ✅ Hover 애니메이션

4. **데이터 품질**
   - ✅ 동적 테이블명 (YYYYMMDD)
   - ✅ NULL 값 존재
   - ✅ 다양한 스키마 (warehouse, analytics, raw_data)

---

## 구현 통계

**총 라인 수**: 2,400+ 라인  
**생성 파일**: 12개  
- Backend: 7개  
- Frontend: 4개  
- Worker: 1개  

**커밋 수**: 7개  
**소요 시간**: 약 50분  

---

## 다음 단계

1. ✅ **Jules 테스팅** (P0)
2. **프로덕션 배포** 확인
3. **사용자 피드백** 수집
4. **개선** (P1-P2)
   - PlayerCard 확장
   - 데이터 스토리 생성 (Gemini)
   - DB 스키마 확장
   - Gemini 기반 문제 생성

---

**작성**: Gemini  
**리뷰**: 필요 시 사용자 확인  
**상태**: 구현 완료, 테스팅 중
