# QueryCraft GCP 무료 배포 가이드 (Zero Cost)

> 💰 **목표**: 완전 무료로 QueryCraft 운영하기  
> ⏱️ 예상 소요 시간: 약 45-60분

---

## 📋 시작 전 체크리스트

시작하기 전에 다음을 준비하세요:

- [ ] Google 계정 (Gmail)
- [ ] GitHub 계정
- [ ] 신용카드 (GCP 인증용, 과금되지 않음)

---

## Part 1: Supabase 설정 (무료 PostgreSQL)

### Step 1.1: Supabase 가입

1. 브라우저에서 **[supabase.com](https://supabase.com)** 접속
2. 화면 우측 상단의 **"Start your project"** 초록색 버튼 클릭
3. **"Continue with GitHub"** 버튼 클릭 (GitHub 계정으로 가입 권장)
4. GitHub 로그인 → Supabase 권한 승인

### Step 1.2: Organization 생성

1. 처음 로그인하면 Organization 생성 화면이 나타남
2. Organization name: `querycraft` (원하는 이름)
3. **"Create organization"** 버튼 클릭

### Step 1.3: 새 프로젝트 생성

1. 대시보드에서 **"+ New project"** 버튼 클릭 (화면 중앙)
2. 다음 정보 입력:

| 필드 | 입력 값 |
|------|---------|
| **Project name** | `querycraft` |
| **Database Password** | 강력한 비밀번호 입력 (📝 반드시 메모!) |
| **Region** | `Northeast Asia (Seoul)` 선택 |
| **Pricing Plan** | `Free` (기본값) |

3. 하단 **"Create new project"** 초록색 버튼 클릭
4. ⏳ 프로젝트 생성까지 약 2분 대기

### Step 1.4: 데이터베이스 연결 정보 확인

1. 프로젝트 생성 완료 후, 왼쪽 사이드바에서:
   - **⚙️ Settings** (톱니바퀴 아이콘, 맨 아래) 클릭
2. Settings 메뉴에서:
   - **Database** 클릭
3. 화면을 아래로 스크롤하여 **"Connection string"** 섹션 찾기
4. **"URI"** 탭 클릭
5. 연결 문자열 복사 (아래와 같은 형식):

```
postgresql://postgres.xxxxx:[YOUR-PASSWORD]@aws-0-ap-northeast-2.pooler.supabase.com:6543/postgres
```

> ⚠️ `[YOUR-PASSWORD]` 부분을 Step 1.3에서 설정한 실제 비밀번호로 교체하세요!

### Step 1.5: POSTGRES_DSN 형식으로 변환

GitHub Secrets에 저장할 형식으로 변환:

```
host=aws-0-ap-northeast-2.pooler.supabase.com user=postgres.xxxxx password=YOUR_PASSWORD dbname=postgres port=6543 sslmode=require
```

또는 URI 형식 그대로 사용 가능:

```
postgresql://postgres.xxxxx:YOUR_PASSWORD@aws-0-ap-northeast-2.pooler.supabase.com:6543/postgres
```

📝 이 값을 메모장에 저장해두세요. 나중에 GitHub Secrets에 사용합니다.

---

## Part 2: GCP 프로젝트 설정

### Step 2.1: GCP Console 접속 및 로그인

1. 브라우저에서 **[console.cloud.google.com](https://console.cloud.google.com)** 접속
2. Google 계정으로 로그인
3. 처음이라면 서비스 약관 동의

### Step 2.2: 새 프로젝트 생성

1. 화면 최상단 검은색 바에서 **"프로젝트 선택"** 드롭다운 클릭
   - (기본적으로 "My First Project" 또는 프로젝트 이름이 표시됨)
2. 팝업 창 우측 상단의 **"새 프로젝트"** 클릭
3. 프로젝트 정보 입력:

| 필드 | 값 |
|------|-----|
| **프로젝트 이름** | `querycraft` (원하는 이름) |
| **위치** | `조직 없음` (기본값) |

4. **"만들기"** 버튼 클릭
5. ⏳ 약 30초 대기
6. 알림 벨 아이콘에서 "프로젝트 만들기: querycraft" 완료 확인

### Step 2.3: 생성한 프로젝트로 전환

1. 상단 바의 **"프로젝트 선택"** 드롭다운 다시 클릭
2. 방금 만든 **"querycraft"** 프로젝트 클릭

### Step 2.4: 결제 계정 연결 (무료 크레딧)

> ⚠️ 신용카드 등록이 필요하지만 무료 한도 내에서는 과금되지 않습니다.

1. 왼쪽 햄버거 메뉴 (≡) 클릭
2. **"결제"** 클릭
3. **"결제 계정 연결"** 또는 **"결제 계정 관리"** 클릭
4. 결제 정보 입력:
   - 국가: 대한민국
   - 계정 유형: 개인
   - 신용카드 정보 입력
5. **$300 무료 크레딧** 자동 적용됨 (90일간 유효)

### Step 2.5: API 활성화

**Cloud Run API 활성화:**

1. 상단 검색창에 **"Cloud Run"** 입력
2. 결과에서 **"Cloud Run API"** 클릭 (API & Services 섹션)
3. **"사용"** 파란색 버튼 클릭
4. ⏳ 약 30초 대기

**Artifact Registry API 활성화:**

1. 상단 검색창에 **"Artifact Registry"** 입력
2. 결과에서 **"Artifact Registry API"** 클릭
3. **"사용"** 파란색 버튼 클릭

### Step 2.6: Artifact Registry 저장소 생성

1. 왼쪽 햄버거 메뉴 (≡) 클릭
2. **"Artifact Registry"** 클릭 (또는 검색)
3. 상단의 **"+ 저장소 만들기"** 클릭
4. 정보 입력:

| 필드 | 값 |
|------|-----|
| **이름** | `query-craft` |
| **형식** | `Docker` |
| **모드** | `표준` |
| **위치 유형** | `리전` |
| **리전** | `us-central1 (아이오와)` ⚡ **중요!** |

5. 하단 **"만들기"** 버튼 클릭

---

## Part 3: 서비스 계정 생성 (GitHub Actions용)

### Step 3.1: 서비스 계정 생성

1. 왼쪽 햄버거 메뉴 (≡) 클릭
2. **"IAM 및 관리자"** → **"서비스 계정"** 클릭
3. 상단 **"+ 서비스 계정 만들기"** 클릭
4. 정보 입력:

| 필드 | 값 |
|------|-----|
| **서비스 계정 이름** | `github-deployer` |
| **서비스 계정 ID** | `github-deployer` (자동 입력됨) |
| **설명** | `GitHub Actions 배포용` |

5. **"만들고 계속하기"** 클릭

### Step 3.2: 권한 부여

1. **"역할 선택"** 드롭다운 클릭
2. 다음 역할을 하나씩 추가 (각각 **"+ 다른 역할 추가"** 클릭):

| 역할 이름 | 검색어 |
|----------|--------|
| **Cloud Run 관리자** | `Cloud Run Admin` |
| **Artifact Registry 작성자** | `Artifact Registry Writer` |
| **서비스 계정 사용자** | `Service Account User` |

3. **"계속"** 클릭
4. **"완료"** 클릭

### Step 3.3: JSON 키 생성

1. 서비스 계정 목록에서 방금 만든 **"github-deployer@..."** 클릭
2. 상단 탭에서 **"키"** 클릭
3. **"키 추가"** → **"새 키 만들기"** 클릭
4. 키 유형: **"JSON"** 선택
5. **"만들기"** 클릭
6. 📥 JSON 파일이 자동 다운로드됨 (이 파일을 안전하게 보관!)

---

## Part 4: GitHub Secrets 설정

### Step 4.1: GitHub 저장소로 이동

1. GitHub에서 QueryCraft 저장소 열기
2. 상단 탭에서 **"Settings"** 클릭

### Step 4.2: Secrets 설정

1. 왼쪽 사이드바에서 **"Secrets and variables"** → **"Actions"** 클릭
2. **"New repository secret"** 버튼 클릭
3. 다음 Secrets를 하나씩 추가:

| Name | Value |
|------|-------|
| `GCP_PROJECT_ID` | GCP 프로젝트 ID (예: `querycraft-123456`) |
| `GCP_SA_KEY` | 다운로드한 JSON 키 파일의 **전체 내용** |
| `POSTGRES_DSN` | Part 1에서 메모한 Supabase 연결 문자열 |
| `GEMINI_API_KEY` | Google AI Studio에서 발급받은 키 |
| `VITE_MIXPANEL_TOKEN` | Mixpanel 토큰 (없으면 `dummy` 입력) |

> 💡 **GCP 프로젝트 ID 확인 방법**:  
> GCP Console 상단 프로젝트 선택 드롭다운 → 프로젝트 이름 옆 ID 확인

---

## Part 5: 예산 알림 설정 (안전장치)

### Step 5.1: 예산 만들기

1. GCP Console → 왼쪽 메뉴 → **"결제"**
2. 왼쪽에서 **"예산 및 알림"** 클릭
3. **"+ 예산 만들기"** 클릭
4. 정보 입력:

| 필드 | 값 |
|------|-----|
| **이름** | `무료 한도 알림` |
| **프로젝트** | `querycraft` 선택 |
| **예산 금액** | `$1` |

5. 임계값 설정:
   - 50% → 이메일 알림
   - 90% → 이메일 알림
   - 100% → 이메일 알림

6. **"완료"** 클릭

---

## Part 6: 배포 실행

### Step 6.1: 코드 푸시

```bash
git add .
git commit -m "Configure GCP free tier deployment"
git push origin main
```

### Step 6.2: 배포 확인

1. GitHub 저장소 → **"Actions"** 탭
2. 워크플로우 실행 상태 확인 (✅ 녹색이면 성공)

### Step 6.3: Cloud Run URL 확인

1. GCP Console → Cloud Run
2. `query-craft-frontend` 서비스 클릭
3. 상단의 URL 확인 (예: `https://query-craft-frontend-xxxxx-uc.a.run.app`)

---

## 🎉 완료!

축하합니다! 이제 QueryCraft가 완전 무료로 운영됩니다.

### 예상 월 비용: **$0**

| 항목 | 비용 |
|------|------|
| Cloud Run (us-central1) | $0 |
| Supabase (무료 티어) | $0 |
| Artifact Registry | $0 |
| **총계** | **$0/월** |

---

## 🔧 문제 해결

### "권한 거부" 오류
- 서비스 계정에 모든 역할이 부여되었는지 확인

### "이미지를 찾을 수 없음" 오류
- Artifact Registry가 `us-central1`에 생성되었는지 확인
- deploy.yml의 리전이 `us-central1`인지 확인

### Supabase 연결 오류
- POSTGRES_DSN의 비밀번호가 올바른지 확인
- `sslmode=require`가 포함되어 있는지 확인

---

## Part 7: Dev/Prod 개발 워크플로우

효율적인 개발과 안정적인 운영을 위해 다음과 같은 브랜치 전략을 권장합니다.

### 7.1 브랜치 역할

| 브랜치 | 용도 | 데이터베이스 | 배포 환경 |
|--------|------|------------|----------|
| `dev` | 일상 개발 및 테스트 | 사내 PostgreSQL (192.168.101.224) | 로컬 Docker |
| `main` | 상용 서비스 배포 | Supabase (Cloud) | GCP Cloud Run |

### 7.2 일상 개발 흐름 (dev)

1. **개발 시작**: `git checkout dev`
2. **코드 작성 및 로컬 테스트**:
   - `docker compose -f docker-compose.dev.yml up -d`
   - 프론트엔드: `http://localhost:15173`
   - 백엔드: `http://localhost:15174`
3. **코드 푸시**: `git push origin dev`

### 7.3 상용 배포 흐름 (main)

1. **기능 검증 완료 후**: `git checkout main`
2. **변경사항 병합**: `git merge dev`
3. **운영 서버 배포**: `git push origin main`
   - GitHub Actions가 자동으로 빌드 및 배포를 수행합니다.
   - 약 3-5분 후 서비스에 반영됩니다.

---

## 🎉 완료!

축하합니다! 이제 QueryCraft가 완전 무료로 운영됩니다.
