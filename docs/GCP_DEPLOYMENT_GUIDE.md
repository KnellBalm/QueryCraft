# GCP 배포 및 운영 가이드

이 문서는 QueryCraft 서비스를 Google Cloud Platform(GCP)에 배포하고 관리하는 방법을 설명합니다.

## 1. 개요
우리는 비용 효율적이고 확장이 용이한 **Serverless 아키텍처**를 사용합니다.
- **Backend / Frontend**: Google Cloud Run
- **Database**: Google Cloud SQL (PostgreSQL)
- **Object Storage**: Google Cloud Storage (GCS)
- **Registry**: Artifact Registry
- **CI/CD**: GitHub Actions

---

## 2. 사전 준비 (GCP Console 세팅)

### 2.1 프로젝트 및 API 활성화
1. [GCP Console](https://console.cloud.google.com/)에서 새 프로젝트 생성.
2. 아래 API들을 활성화합니다:
   - Cloud Run API
   - Artifact Registry API
   - Cloud SQL Admin API
   - Compute Engine API (VPC용)

### 2.2 리소스 생성
1. **Artifact Registry**: `query-craft` 리포지토리 생성 (Region: `asia-northeast3`).
2. **Cloud SQL**: PostgreSQL 인스턴스 생성.
   - 공개 IP 비활성화 및 비공개 IP(VPC) 사용 권장.
   - 데이터베이스(`pa_lab`) 및 사용자 생성.
3. **Cloud Storage (선택)**: DuckDB 데이터베이스 파일 백업 및 문제 JSON 저장을 위한 버킷 생성.

### 2.3 서비스 계정 설정
1. IAM에서 Github Actions용 서비스 계정(`github-deployer`) 생성.
2. 아래 권한(Role) 부여:
   - Cloud Run Admin
   - Artifact Registry Writer
   - Storage Admin
   - Service Account User
3. JSON 키를 생성하여 저장해둡니다.

---

## 3. GitHub 설정

GitHub Repository의 **Settings > Secrets and variables > Actions**에 아래 보안 변수들을 등록합니다:

| Name | Description |
|------|-------------|
| `GCP_PROJECT_ID` | GCP 프로젝트 ID |
| `GCP_SA_KEY` | 서비스 계정 JSON 키 내용 |
| `POSTGRES_DSN` | Cloud SQL 접속 정보 (`host=... user=... password=... dbname=...`) |
| `GEMINI_API_KEY` | Google Gemini API 키 |
| `VITE_MIXPANEL_TOKEN` | Mixpanel 토큰 (빌드 타임에 주입) |

---

## 4. 배포 프로세스

### 4.1 자동 배포 (CI/CD)
- `main` 브랜치에 코드를 푸시하거나 PR을 머지하면 `.github/workflows/deploy.yml` 워크플로우가 실행됩니다.
- 빌드 -> Docker 이미지 푸시 -> Cloud Run 배포 순으로 진행됩니다.

### 4.2 수동 배포
필요한 경우 로컬 명령어로 배포할 수 있습니다 (gcloud SDK 설치 필요).

```bash
# 백엔드 배포 예시
gcloud run deploy query-craft-backend \
  --source . \
  --region asia-northeast3 \
  --set-env-vars "POSTGRES_DSN=...,GEMINI_API_KEY=..."
```

---

## 5. 운영 및 모니터링

### 5.1 로그 확인
- [Cloud Logging](https://console.cloud.google.com/logs/query)에서 서비스 로그를 실시간으로 확인할 수 있습니다.
- `resource.type="cloud_run_revision"` 필터 사용.

### 5.2 데이터베이스 관리
- Cloud SQL의 **Query Insights**를 통해 성능이 저하되는 쿼리를 트래킹할 수 있습니다.
- 정기적인 자동 백업 설정을 확인하세요.

### 5.3 비용 관리
- **Cloud Run**: 트래픽이 없을 때 0으로 스케일되어 유휴 비용이 거의 없습니다.
- **Cloud SQL**: 가장 낮은 사양(`db-f1-micro`)으로 시작하여 필요시 업그레이드하세요.

---

## 6. 트러블슈팅

### 6.1 CORS 이슈
- 프론트엔드와 백엔드 도메인이 다를 경우 FastAPI의 `CORSMiddleware` 설정을 확인해야 합니다.
- `backend/main.py`에서 `allow_origins`에 프론트엔드 URL을 추가하세요.

### 6.2 Cloud SQL 연결 실패
- Cloud Run 설정에서 **Cloud SQL 연결**이 설정되어 있는지 확인하세요.
- IAM 권한에 `Cloud SQL Client`가 포함되어 있어야 합니다.
