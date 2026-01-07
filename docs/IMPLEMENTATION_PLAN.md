# QueryCraft Implementation Plan (2026-01-07 업데이트)

## 🎯 오늘 완료된 작업 (2026-01-07)

### 1. 로그인 세션 수정 ✅
- `secure=True`, `samesite='none'` 쿠키 설정 추가
- HTTPS 크로스 도메인 환경에서 세션 유지 문제 해결
- CORS 설정 개선 (`*.run.app` 도메인 허용)

### 2. MSA 아키텍처 구현 ✅
```
Cloud Run (API)              Cloud Functions (Workers)
├── 쿼리 에디터               ├── problem-worker
├── 사용자 API                └── tip-worker
├── 채점 조회                
└── 관리자 API            → Supabase (PostgreSQL)
```

**생성된 파일:**
- `shared/gemini_models.py` - 멀티모델 Gemini 클래스
- `functions/problem_worker/main.py` - 문제 생성 워커
- `functions/tip_worker/main.py` - 팁 생성 워커
- `functions/deploy.sh` - 수동 배포 스크립트

### 3. 멀티모델 Gemini 구현 ✅
| 용도 | 모델 |
|------|------|
| 문제 생성 | gemini-2.5-flash |
| 채점 | gemini-2.5-flash |
| 오늘의 팁/힌트 | gemini-2.5-flash-lite |
| 에러 설명 | gemini-3-flash |

### 4. 새 DB 테이블 추가 ✅
- `problems` - 문제 저장 (파일 → DB 이전용)
- `daily_tips` - 오늘의 SQL 팁
- `worker_logs` - Cloud Functions 실행 로그

### 5. GitHub Actions 수정 ✅
- Cloud Functions 배포 스텝 추가
- Cloud Scheduler 설정 스텝 추가
- `continue-on-error` 추가로 실패해도 배포 진행

### 6. 서버 시작 최적화 ✅
- 스케줄러 제거 (Cloud Functions 대체)
- DB 초기화 백그라운드 실행
- 시작 타임아웃 문제 해결

---

## ⏳ 배포 대기 중

### Cloud Functions API 활성화
- [x] cloudfunctions.googleapis.com
- [ ] cloudscheduler.googleapis.com
- [ ] cloudbuild.googleapis.com

> API 전파 완료 후 배포 재실행 필요

---

## 📋 다음 단계 (남은 작업)

### 집에서 할 일

#### 1. Cloud Functions 배포 확인
```bash
# GCP 콘솔에서 확인
https://console.cloud.google.com/functions?project=querycraft-483512
```
- problem-worker 함수 존재 확인
- tip-worker 함수 존재 확인

#### 2. Cloud Scheduler 설정 확인
```bash
https://console.cloud.google.com/cloudscheduler?project=querycraft-483512
```
- problem-generation-daily (매일 KST 01:00)
- tip-generation-daily (매일 KST 00:30)

#### 3. 문제 생성 테스트
- 관리자 페이지 → 문제 생성 버튼 클릭
- 또는 Cloud Functions 직접 호출:
```bash
curl -X POST https://us-central1-querycraft-483512.cloudfunctions.net/problem-worker
```

#### 4. 서비스 동작 확인
- [ ] 문제 목록 표시
- [ ] SQL 실행 기능
- [ ] 채점 기능
- [ ] 리더보드

---

## 🔧 문제 발생 시 대응

### Cloud Functions 배포 실패
1. GCP Console → API 및 서비스 → 라이브러리
2. 다음 API 활성화:
   - Cloud Functions API
   - Cloud Build API
   - Cloud Scheduler API
3. 5분 대기 후 GitHub Actions 재실행

### 문제 생성 실패 (429 에러)
- Gemini 무료 할당량 초과
- 해결: 다른 모델로 변경 또는 1시간 대기

### 서버 시작 실패
- GCP 로그 확인: 구체적 에러 메시지
- Import 에러 시 누락된 함수 확인

---

## 📊 현재 시스템 상태

| 컴포넌트 | 상태 |
|----------|------|
| Cloud Run Backend | ✅ 배포 완료 |
| Cloud Run Frontend | ✅ 배포 완료 |
| Supabase DB | ✅ 연결됨 |
| Cloud Functions | ⏳ API 전파 대기 |
| Cloud Scheduler | ⏳ 설정 대기 |
| 멀티모델 Gemini | ✅ 코드 완료 |

---

## 🚀 장기 로드맵

### 이번 주
- [x] MSA 아키텍처 구현
- [x] 멀티모델 Gemini
- [ ] Cloud Functions 배포 완료
- [ ] 문제 생성 정상화

### 다음 주
- [ ] 문제 조회를 DB 기반으로 전환
- [ ] 할당량 모니터링 대시보드
- [ ] 폴백 로직 (모델 실패 시 대체)

### 향후
- [ ] A/B 테스트 기능
- [ ] 문제 풀 미리 생성 (여러 날짜)
- [ ] 사용자 피드백 기반 문제 개선
