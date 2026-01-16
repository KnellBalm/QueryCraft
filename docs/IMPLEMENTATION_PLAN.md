# Phase 2: 서비스 오픈 안정화 및 기능 고도화 계획

> 📅 시작일: 2026-01-17

## 현재 상황 분석

### 🔴 긴급 이슈 (P0)

| 이슈 | 원인 분석 | 수정 방안 |
|-----|---------|---------|
| 로그인 모달 UX | 오버레이 클릭 시 모달 닫힘 (`LoginModal.tsx` line 55) | 오버레이 onClick 제거, X 버튼으로만 닫기 |
| 로그인 401 에러 | 등록되지 않은 계정 또는 잘못된 비밀번호 | 테스트 계정 생성/확인, 로그 분석 |
| 스케줄러 미동작 | Cloud Run scale-to-zero 시 APScheduler 중지 | Cloud Scheduler 설정 확인 및 재설정 |
| 15/16일 데이터 누락 | 스케줄러 미동작으로 문제/데이터 미생성 | 수동 생성 또는 Cloud Scheduler 재설정 |

---

## Proposed Changes

### 1. 긴급 이슈 해결

#### [MODIFY] [LoginModal.tsx](file:///mnt/z/GitHub/QueryCraft/frontend/src/components/LoginModal.tsx)
- 오버레이 클릭으로 모달 닫기 제거
- X 버튼 또는 ESC 키로만 닫도록 수정

#### [VERIFY] 로그인 401 에러
1. Supabase DB에서 테스트 사용자 확인
2. 백엔드 로그 분석
3. 테스트 계정 생성

#### [VERIFY] Cloud Scheduler 상태
1. GCP Console에서 Cloud Scheduler 작업 확인
2. `/admin/schedule/run` 호출 이력 확인
3. 실패 시 재시도/알림 설정

---

### 2. 문제 생성 안정화 (P1)

#### [MODIFY] SQL 검증 루프 강화
- Gemini 생성 SQL을 DuckDB `EXPLAIN`으로 검증
- 실패 시 최대 3회 재시도 (지수 백오프)
- `dataset_versions` 테이블에 실패 기록

#### [ADD] 데이터 롤백 기능
- `POST /admin/rollback/{date}` 엔드포인트 추가
- 특정 날짜 데이터 즉시 롤백 가능

---

### 3. 데이터 생성 엔진 고도화 (P1)

#### [ADD] 신규 분석 시나리오
- 퍼널 분석: 회원가입 → 첫 구매 → 재구매
- 잔존율: D1, D7, D30 Retention
- LTV 예측: 사용자별 누적 결제 시계열

#### [ADD] RCA용 이상치 데이터
- 광고 채널 효율 급락 (CTR 50% 하락)
- 결제 대기 시간 증가 (특정 지역 3배)
- 리텐션 급락 (특정 코호트)

---

### 4. 추가 기능 설계 (P2)

#### [DESIGN] 맞춤형 로드맵
- 사용자 풀이 이력 분석 (정답률, 취약 토픽)
- 추천 알고리즘 설계
- API: `GET /api/recommend/roadmap`

#### [DESIGN] 소셜 피드백 시스템
- 쿼리 결과 공유: `POST /api/share`
- 피드백 수집: `POST /api/feedback`

---

## Jules 위임 업무

```bash
# Jules-1: 백엔드 테스트 커버리지 80%
jules new "backend/ 디렉토리의 테스트 커버리지를 80%까지 높이세요..."

# Jules-2: API 및 프로젝트 문서화
jules new "프로젝트 문서를 최신화하고 자동화하세요..."

# Jules-3: 프론트엔드 코드 품질 개선
jules new "frontend/src/의 TypeScript 타입 안정성을 강화하세요..."
```

---

## Verification Plan

### Automated Tests
```bash
pytest tests/ -v --cov=backend
cd frontend && npm run build
```

### Manual Verification
1. 로그인 모달 UX 확인 (오버레이 클릭 무시)
2. 테스트 계정 로그인 성공 확인
3. `/admin/schedule/run` 수동 호출 → 오늘 날짜 문제 생성 확인
4. SQL 검증 재시도 로직 로그 확인
