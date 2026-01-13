# QueryCraft GCP 무료 배포 및 운영 가이드

> **목표**: 상용 서버(GCP)와 데이터베이스(Supabase)를 활용하여 QueryCraft를 완전 무료(Zero Cost)로 운영하기

---

## 🏗️ 상용 시스템 아키텍처

GCP로 배포되는 상용 버전은 다음과 같은 구조로 작동합니다:

- **Frontend**: GCP Cloud Run (Docker 기반)
- **Backend/Scheduler**: GCP Cloud Run (Docker 기반, APScheduler 내장)
- **Database**: Supabase (PostgreSQL 15+)
- **CI/CD**: GitHub Actions (main 브랜치 push 시 자동 빌드 및 배포)

---

## 🗝️ 필수 환경 변수 (GitHub Secrets)

GCP 배포 시 GitHub Actions 단계에서 동적으로 주입되어야 하는 핵심 설정입니다.

| 변수명 | 설명 | 중요도 |
|:---:|:---|:---:|
| `POSTGRES_DSN` | Supabase의 PostgreSQL 연결 URI | **P0** |
| `GEMINI_API_KEY` | Google Gemini Pro API 키 | **P0** |
| `SCHEDULER_API_KEY` | Cloud Scheduler 연동용 보안 토큰 | **P0** |
| `ENV` | `production`으로 설정 필수 | **P1** |
| `VITE_API_URL` | 배포된 백엔드 서비스의 URL (프론트엔드용) | **P1** |

---

## 🕒 타임존 및 스케줄링 핵심 전략 (KST 통합)

GCP의 Cloud Run 환경은 기본적으로 **UTC** 시간대를 사용합니다. QueryCraft는 이를 보정하기 위해 다음과 같은 전략을 사용합니다.

### 1. 백엔드 KST 보정
백엔드에는 `backend/common/date_utils.py`가 포함되어 있어, 서버의 물리적 타임존과 상관없이 모든 날짜 계산을 한국 시간(KST)으로 처리합니다. 따라서 별도의 서버 타임존 설정이 필요 없습니다.

### 2. Cloud Scheduler 연동 (새벽 1시 실행)
매일 새로운 문제를 생성하기 위해 GCP Cloud Scheduler를 사용합니다. KST 자정 이후(새벽 1시 권장)에 트리거하도록 설정해야 합니다.

- **설정 시간 (Cron)**: `0 1 * * *` (KST 기준)
- **타임존 설정**: `Asia/Seoul` 선택
- **대상 URL**: 배포된 백엔드의 `/admin/trigger/daily-generation` 엔드포인트
- **헤더**: `X-Scheduler-Key: {{SCHEDULER_API_KEY}}`

---

## 🚀 배포 단계 (Quick Start)

### Step 1: Supabase 프로젝트 생성
1. [Supabase](https://supabase.com)에서 새로운 프로젝트를 생성합니다. (Region: Seoul)
2. Database Settings에서 Connection String(URI)을 복사해둡니다.

### Step 2: GCP 프로젝트 설정
1. [GCP Console](https://console.cloud.google.com)에서 프로젝트를 생성합니다.
2. Cloud Run 및 Artifact Registry API를 활성화합니다.
3. GitHub Actions 배포를 위한 서비스 계정(Service Account)을 생성하고 키(JSON)를 발급받습니다.

### Step 3: GitHub Secrets 등록
상단의 '필수 환경 변수' 표를 참고하여 GitHub 저장소의 `Settings > Secrets and variables > Actions` 메뉴에서 모든 값을 등록합니다.

### Step 4: 배포 실행
1. `dev` 브랜치에서 개발 및 검증을 마칩니다.
2. `main` 브랜치로 코드를 병합(merge) 한 뒤 `push` 합니다.
3. GitHub Actions 탭에서 배포 프로세스가 완료되는 것을 기다립니다.

---

## 🛠️ 운영 및 모니터링

- **시스템 상태 확인**: 프론트엔드의 `/admin` 페이지에서 스케줄러 상태와 로그를 실시간으로 확인할 수 있습니다.
- **수동 문제 생성**: 문제가 제때 생성되지 않았을 경우, 관리자 대시보드에서 `수동 생성` 버튼을 통해 즉시 보정이 가능합니다.
- **비용 모니터링**: Supabase 무료 티어(500MB)와 GCP Cloud Run 무료 한도를 초과하지 않도록 정기적으로 사용량을 확인하세요.

---

## ⚠️ 주의사항

- **PostgreSQL 전용**: Supabase(PostgreSQL)를 사용하므로, 쿼리 작성 시 PostgreSQL 표준 문법을 준수해야 합니다.
- **콜드 스타트(Cold Start)**: Cloud Run 무료 티어 사용 시 첫 접속 시 로딩이 수 초간 지연될 수 있습니다.

---

**GCP와 함께 QueryCraft의 안정적인 상용 서비스를 경험해보세요!**
