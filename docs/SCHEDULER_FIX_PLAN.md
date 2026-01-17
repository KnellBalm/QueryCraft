# scheduler_fix_plan.md

스케줄러 아키텍처를 개선하고 누락된 데이터(1월 15~17일)를 복구하기 위한 계획입니다.

## 1. 현재 문제점
- **아키텍처 취약성**: Cloud Scheduler가 백엔드를 찌르고, 백엔드가 `subprocess`로 `gcloud`를 호출하여 Job을 실행하는 구조임. 그러나 백엔드 컨테이너에는 `gcloud`가 설치되어 있지 않아 실행 실패.
- **백필 기능 부재**: `worker/main.py`가 날짜 파라미터를 받지 않아 과거 날짜 문제 생성이 어려움.
- **환경변수 오염**: `POSTGRES_DSN` 뒤에 개행 문자가 포함되어 일부 서비스에서 연결 오류 가능성 있음.
- **인증 불일치**: 로컬과 상용의 `SCHEDULER_API_KEY`가 달라 수동 테스트 및 검증이 어려움.

## 2. 제안하는 개선안

### 아키텍처 변경
- **Direct Job Trigger**: Cloud Scheduler가 백엔드를 거치지 않고 Cloud Run Job Execution API를 직접 호출하도록 변경.
- **IAM 권한 부여**: 기본 서비스 계정에 Cloud Run Job을 실행할 수 있는 `roles/run.developer` 권한 부여.

### 기능 강화
- **Worker Backfill**: `worker/main.py`에 `--date` 인자를 추가하여 특정 날짜의 문제를 생성할 수 있도록 수정 (완료).

### 인프라 최적화
- **Environ Cleanup**: `deploy.yml`에서 비밀번호 등 환경변수 주입 시 개행 문자를 제거하도록 수정.

## 3. 상세 작업 내역

### [Component] Infrastructure - Github Actions
- **[MODIFY] [deploy.yml](file:///mnt/z/GitHub/QueryCraft/.github/workflows/deploy.yml)**: 
  - `POSTGRES_DSN` 등의 환경변수 설정 시 `${{ secrets.POSTGRES_DSN }}` 대신 개행이 제거된 값을 사용하도록 수정.
  - `Setup Cloud Scheduler` 단계에서 백엔드 URI 대신 Cloud Run Job API URI를 사용하도록 변경.
  - `oidc-service-account-email` 설정 추가.

### [Component] Backend - Admin API
- **[MODIFY] [admin.py](file:///mnt/z/GitHub/QueryCraft/backend/api/admin.py)**:
  - 더 이상 사용되지 않는 `gcloud` 호출 로직을 제거하거나, API 호출 방식으로 전환 고려 (일단 직접 트리거 방식으로 변경되므로 우선순위 낮음).

## 4. 복구 작업 (Backfill)
1. `deploy.yml` 변경사항 푸시 및 배포 완료.
2. `gcloud run jobs execute` 명령어를 사용하여 1월 15일, 16일, 17일 데이터 수동 생성.

## 5. 검증 계획
- Cloud Scheduler 콘솔에서 '지금 실행'을 눌러 Job이 정상적으로 트리거되는지 확인.
- DB에서 1월 15~17일 데이터가 정상적으로 생성되었는지 쿼리로 확인.
