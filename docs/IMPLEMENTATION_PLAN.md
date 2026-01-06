# QueryCraft 구현 계획 및 업무 인수인계 (2026-01-07)

## 📋 현재 상태 요약

### 1. 배포 상황
- **GCP Cloud Run**: 배포 성공 (✅ 녹색)
- **Supabase**: 배포는 성공했으나 테이블이 아직 자동으로 생성되지 않음.
  - **원인 추정**: 백엔드 시작 시 Supabase 연결에 실패했거나, SSL 설정 문제로 초기화 스크립트가 실행되지 않았을 가능성 높음.
  - **조치**: `main.py`에 에러 핸들링을 추가하여 앱 시작은 가능하게 해둠.

### 2. 환경 분리
- **Prod**: `main` 브랜치 (GCP + Supabase)
- **Dev**: `dev` 브랜치 (내부 워크스테이션 + 192.168.101.224 PostgreSQL)

---

## 🚀 내일 회사에서 해야 할 일 (To-Do)

### 1. 환경 준비
- `dev` 브랜치로 전환: `git checkout dev`
- 최신 코드 가져오기: `git pull origin dev`
- 로컬 개발 환경 실행: `docker compose -f docker-compose.dev.yml up -d`

### 2. Supabase 테이블 생성 문제 해결
- **GCP Cloud Run 로그 확인**: 
  - 콘솔에서 `query-craft-backend` 로그 확인.
  - `[WARNING] Database initialization failed` 메시지가 있는지 확인.
- **수동 초기화 시도**:
  - 만약 자동 생성이 계속 안 된다면, 백엔드 URL의 `/docs` (Swagger)에서 초기화 API를 호출하는 기능을 추가하거나, Supabase SQL Editor에서 `sql/init.sql` 내용을 직접 실행.

### 3. 회원가입 및 온보딩 버그 수정
- **회원가입**: `users` 테이블 생성 확인 후 테스트.
- **온보딩 6단계**: 프론트엔드 네트워크 탭에서 어떤 API가 무한 로딩인지 확인.

### 4. 디렉토리 구조 개편 (안정화 후)
- 루트의 파편화된 폴더들을 `backend/` 내부로 통합.

---

## 🛠️ Antigravity를 위한 가이드
내일 회사에서 Antigravity에게 다음과 같이 요청하세요:
> "QueryCraft 프로젝트 작업을 이어서 할 거야. `docs/IMPLEMENTATION_PLAN.md` 파일을 읽고 현재 상태와 내일 할 일을 파악해줘. 먼저 Supabase 테이블이 안 생기는 문제부터 조사하자."

---

## 📝 주요 변경 파일 기록
- `backend/services/db_init.py`: DB 테이블 생성 스크립트
- `backend/main.py`: 시작 시 초기화 로직 (try-except 적용)
- `docs/GCP_DEPLOYMENT_GUIDE.md`: 최신 배포 및 워크플로우 가이드
- `docker-compose.dev.yml`: 로컬 개발용 설정
