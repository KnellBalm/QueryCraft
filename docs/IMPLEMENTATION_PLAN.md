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

### [MODIFY] [data_generator_advanced.py](file:///home/naca11/QueryCraft/backend/generator/data_generator_advanced.py)
DuckDB 의존성을 제거하고 모든 데이터(PA, Stream)를 Supabase(PostgreSQL)에 생성하도록 수정합니다. `TRUNCATE CASCADE`를 적용하여 외래 키 문제를 해결합니다.

### [MODIFY] [problem_service.py](file:///home/naca11/QueryCraft/backend/services/problem_service.py)
`get_table_schema` 함수가 DuckDB를 거치지 않고 PostgreSQL의 `information_schema`에서 모든 분석용 테이블 정보를 가져오도록 수정합니다.

### [MODIFY] [MainPage.tsx](file:///home/naca11/QueryCraft/frontend/src/pages/MainPage.tsx) / [Workspace.tsx](file:///home/naca11/QueryCraft/frontend/src/pages/Workspace.tsx)
API 응답이 배열이 아닌 경우(에러 등)에 대비하여 `.map()` 호출 전 방어 코드를 추가하거나 초기값을 엄격히 관리합니다.

---

## 2026-01-08: 데이터셋 Supabase 통합 및 안정성 개선

### 이슈 사항
1. **프론트엔드 크래시**: API 에러 응답 시 `.map()` 호출로 인한 런타임 오류.
2. **테이블 누락**: `pa_events` 등 분석용 테이블이 로컬 DB나 DuckDB에 분산되어 있어 사용자가 찾지 못함.

### 변경 사항

#### [DB/Generator] 데이터셋 Supabase 통합
- `data_generator_advanced.py`: `run_stream`, `run_pa`가 오직 PostgreSQL(Supabase)만 사용하도록 변경.
- `init_postgres_schema`: 모든 테이블(`pa_`, `stream_`) 생성 보장.
- `truncate_targets`: `TRUNCATE ... CASCADE` 적용.

#### [Backend] 서비스 로직 통합
- `problem_service.py`: `get_table_schema` 통합.
- `database.py`: 커넥션 관리 재점검.

#### [Frontend] 런타임 에러 방지
- `Array.isArray()` 체크 또는 기본값 `[]` 강제 적용.

### [MODIFY] [nginx.conf](file:///home/naca11/QueryCraft/frontend/nginx.conf)
Nginx 시작 시 호스트 해석 실패로 인한 컨테이너 실행 오류(Cloud Run)를 방지하기 위해 `proxy_pass` 설정을 변수 방식으로 변경합니다.

### [MODIFY] [client.ts](file:///home/naca11/QueryCraft/frontend/src/api/client.ts)
개발 서버에서 IP로 접속 시 직접 백엔드 포트(15174)를 호출하여 CORS 오류가 발생하는 것을 방지하기 위해, 상대 경로 `/api`를 사용하여 Nginx 프록시를 경유하도록 수정합니다.

---

## 2026-01-08: 프론트엔드 배포 및 CORS 이슈 해결

### 이슈 사항
1. **Cloud Run 배포 실패**: `nginx.conf`에 추가된 `http://backend:8000/`을 Nginx 시작 시 해석하려다 실패함.
2. **개발 서버 CORS**: 프론트엔드에서 직접 백엔드 포트를 호출하여 브라우저 정책에 걸림.

### 변경 사항

#### [MODIFY] [nginx.conf](file:///home/naca11/QueryCraft/frontend/nginx.conf)
- `resolver` 추가 및 `set` 변수를 사용한 `proxy_pass` 설정 (Lazy resolution).
- 이로 인해 운영 환경에서 `backend` 호스트가 없어도 Nginx가 정상 시작됨.

#### [MODIFY] [client.ts](file:///home/naca11/QueryCraft/frontend/src/api/client.ts)
- `VITE_API_URL`이 없는 경우 기본값을 `/api` (상대 경로)로 설정.
- 개발 서버(15173)에서 `/api`로 요청 시 Nginx가 이를 백엔드(15174)로 포워딩하여 CORS 우회.

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
