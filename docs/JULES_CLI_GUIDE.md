# Jules CLI 완벽 가이드

## 📖 Jules란?

**Jules**는 Google이 개발한 **비동기 AI 코딩 에이전트**로, Google AI Studio를 통해 제공됩니다.

### 핵심 특징
- 🤖 **자율적**: 버그 수정, 기능 추가, 테스트 작성, 문서화 등을 독립적으로 수행
- ⚡ **비동기**: 작업을 백그라운드에서 실행하여 개발자는 다른 작업 가능
- ☁️ **클라우드 기반**: 안전한 VM에서 코드 복제, 의존성 설치, 파일 수정 자동 수행
- 🔗 **GitHub 통합**: 저장소 클론, 브랜치 생성, PR 작성 자동화
- 📊 **성능**: 코딩 벤치마크에서 **63.8% 정확도** (Gemini CLI보다 우수)

---

## 🎯 Jules가 할 수 있는 것

### 1. 핵심 개발 작업

| 작업 유형 | 설명 | 예시 |
|---------|------|------|
| 🐛 **버그 수정** | 에러 로그를 분석하여 버그 수정 | "NaN 값 처리 버그 수정" |
| ✨ **기능 추가** | 새로운 기능 구현 | "헬스체크 API 엔드포인트 추가" |
| 📝 **문서화** | 코드, API, README 문서 작성 | "모든 API에 대한 OpenAPI 스키마 작성" |
| 🧪 **테스트 작성** | 유닛/통합 테스트 자동 생성 | "pytest 테스트 커버리지 80% 달성" |
| ⚡ **성능 개선** | 코드 최적화 및 리팩토링 | "DataFrame 비교 로직 벡터화" |
| 🔄 **리팩토링** | 코드 구조 개선, 중복 제거 | "함수를 50줄 이하로 분리" |
| 🔧 **의존성 관리** | 패키지 업데이트, 호환성 수정 | "Python 3.12로 업그레이드" |

### 2. 고급 기능

- **파일 스코핑**: 작업 범위를 특정 파일/디렉토리로 제한
- **메모리 기능**: 사용자 선호도 기억 및 미래 작업에 적용
- **환경 변수**: 프로젝트별 설정 정의 가능
- **CI/CD 통합**: GitHub Actions, GitLab CI 등과 연동
- **이슈 트래커 통합**: Jira, Linear 등과 자동 연동
- **통신 도구 연동**: Slack 알림 등 workflow 자동화

---

## ⚠️ Jules의 제한사항

### 1. 감독 필요
- **"유능한 주니어 개발자"** 수준
- AI가 생성한 코드는 **반드시 검토 필요**
- 미묘한 버그나 환경 차이로 인한 에러 가능

### 2. 사용 제한

| 항목 | 무료 티어 | AI Pro | AI Ultra |
|------|----------|--------|----------|
| 일일 작업 수 | 제한적 | 더 많음 | 최대 |
| 모델 접근 | 기본 | Gemini 3 Pro | 우선 접근 |
| 비용 | 무료 | 유료 | 유료 |

- **처리량 제한**: 일일 작업 수 제한으로 대규모 작업 시 병목 가능
- **리소스 블로킹**: 큰 작업 시 할당량 소진 위험

### 3. 기술적 제한
- **모호한 명령**: 불명확한 지시는 반복 작업 증가
- **내부 라이브러리**: 사내 전용 라이브러리는 이해하기 어려움
- **의존성 오류**: 최신 패키지나 복잡한 환경에서 설치 누락 가능
- **속도**: 계획 수립에 시간 소요 (즉각적인 피드백이 필요한 작업에는 부적합)

### 4. 보안 고려사항
- **클라우드 처리**: 코드가 Google 클라우드에서 처리됨
- **기밀 프로젝트**: 고도로 규제된 산업이나 기밀 프로젝트는 주의 필요
- **기업 거버넌스**: 엔터프라이즈 컴플라이언스 세부사항 미공개

---

## 💡 Jules를 효과적으로 사용하는 방법

### 1. 명확한 작업 지시

#### ❌ 나쁜 예
```bash
jules new "코드 개선"
jules new "버그 수정"
jules new "테스트 추가"
```

#### ✅ 좋은 예
```bash
jules new "backend/services/problem_service.py의 모든 함수를 50줄 이하로 분리하고, 
각 함수에 타입 힌트와 docstring을 추가하세요. 
기능은 변경하지 말고 코드 구조만 개선하세요."

jules new "backend/api/health.py의 HTTP 500 에러 수정:
- NaN 값을 None으로 변환
- float 값 안전하게 직렬화
- 에러 발생 시 로그 기록 추가"

jules new "backend/api/admin.py의 모든 엔드포인트에 대한 pytest 테스트 작성:
- 정상 케이스 (200 OK)
- 인증 실패 (401, 403)
- 잘못된 입력 (400)
- 서버 에러 (500)
각 엔드포인트마다 최소 4개 테스트 케이스"
```

### 2. 작업 범위 제한

**대규모 작업은 분할:**
```bash
# ❌ 너무 큼
jules new "전체 백엔드 리팩토링"

# ✅ 단계별 분할
jules new "Step 1: backend/services/ 디렉토리의 모든 서비스 클래스에 타입 힌트 추가"
# 완료 대기
jules new "Step 2: backend/api/ 디렉토리의 모든 라우터에 OpenAPI 스키마 추가"
# 완료 대기
jules new "Step 3: 모든 데이터베이스 쿼리에 에러 핸들링 추가"
```

### 3. 병렬 실행 활용

**창의적 작업에는 병렬 실행:**
```bash
# 동일 작업을 3번 실행하여 최선의 결과 선택
jules new --parallel 3 "QueryCraft 홈페이지 디자인 개선:
- 현대적인 UI/UX 적용
- 반응형 디자인
- 다크 모드 지원"

# 3개 세션의 결과를 모두 pull하여 비교
jules remote pull --session 123456
jules remote pull --session 123457  
jules remote pull --session 123458

# 최선의 결과 선택 후 적용
jules remote pull --session 123456 --apply
```

### 4. 컨텍스트 제공

**충분한 배경 정보 제공:**
```bash
jules new "backend/scheduler.py 개선:

현재 상황:
- APScheduler를 사용하여 매일 KST 01:00에 문제 생성
- Cloud Run 환경에서 실행 (stateless)
- 중복 실행 방지 로직 필요

개선 사항:
- 실행 기록을 PostgreSQL에 저장
- 중복 실행 방지 락 메커니즘 추가
- 에러 발생 시 재시도 로직 (최대 3회, 지수 백오프)
- 모든 스케줄러 이벤트를 logs 테이블에 기록

변경하지 말아야 할 것:
- 스케줄 시간 (KST 01:00)
- 기존 함수 시그니처"
```

---

## 🚀 QueryCraft 프로젝트 활용 예제

### 예제 1: 테스트 커버리지 개선

```bash
jules new "backend/ 디렉토리의 테스트 커버리지를 80%까지 높이세요:

우선순위:
1. backend/api/ (모든 엔드포인트)
2. backend/services/ (핵심 비즈니스 로직)
3. backend/generator/ (데이터 생성 로직)

각 모듈당:
- 정상 케이스 테스트
- 엣지 케이스 테스트
- 에러 케이스 테스트
- Mock을 사용한 외부 의존성 격리

pytest, pytest-cov 사용"
```

### 예제 2: 성능 최적화

```bash
jules new "backend/services/grading_service.py의 DataFrame 비교 로직 최적화:

현재 문제:
- 행 단위 반복문 사용 (느림)
- 108-142 라인의 이중 for 루프

개선 방법:
- Pandas 벡터화 연산 사용
- numpy 배열 연산 활용
- 성능 벤치마크 코드 추가 (기존 vs 개선)

목표: 10배 이상 성능 향상"
```

### 예제 3: 보안 강화

```bash
jules new "backend/api/auth.py의 비밀번호 해싱 개선:

현재: SHA256 사용 (취약)
변경: bcrypt 사용

작업:
1. requirements.txt에 bcrypt 추가
2. 비밀번호 해싱 함수를 bcrypt로 변경
3. 기존 SHA256 해시 마이그레이션 스크립트 작성
4. 하위 호환성 유지 (기존 사용자 로그인 가능)
5. 테스트 코드 업데이트"
```

### 예제 4: 문서 자동화

```bash
jules new "프로젝트 문서 완성:

1. README.md 업데이트:
   - 프로젝트 개요
   - 설치 방법 (로컬 + Docker)
   - API 엔드포인트 목록
   - 환경 변수 설명
   - 배포 가이드

2. API_REFERENCE.md 생성:
   - 모든 엔드포인트 상세 문서
   - 요청/응답 예시
   - 에러 코드 설명

3. CONTRIBUTING.md 생성:
   - 개발 환경 설정
   - 코드 스타일 가이드
   - PR 프로세스"
```

### 예제 5: 데이터베이스 마이그레이션

```bash
jules new "PostgreSQL 스키마 마이그레이션 시스템 추가:

요구사항:
- Alembic 사용
- 자동 마이그레이션 스크립트 생성
- 롤백 기능
- 마이그레이션 히스토리 관리

작업:
1. alembic 설정 파일 생성
2. 현재 스키마를 초기 마이그레이션으로 생성
3. 마이그레이션 실행 명령어 README에 추가
4. CI/CD 파이프라인에 자동 마이그레이션 통합"
```

---

## 🔧 고급 활용 기법

### 1. GitHub Issues와 통합

```bash
# 나에게 할당된 가장 어려운 이슈를 Jules에 할당
gh issue list --assignee @me --label "bug" --sort created --limit 1 --json title,body | \
  jq -r '.[0] | "[\(.title)]\n\(.body)"' | \
  jules new

# 모든 "enhancement" 이슈를 Jules에 할당
gh issue list --label "enhancement" --json number,title,body | \
  jq -r '.[] | "Issue #\(.number): \(.title)\n\(.body)"' | \
  while read -r issue; do
    echo "$issue" | jules new
  done
```

### 2. CI/CD 통합

```yaml
# .github/workflows/jules-auto-fix.yml
name: Jules Auto-Fix

on:
  issues:
    types: [labeled]

jobs:
  jules-fix:
    if: github.event.label.name == 'auto-fix'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install Jules
        run: npm install -g @google/jules
      - name: Assign to Jules
        run: |
          echo "${{ github.event.issue.title }}: ${{ github.event.issue.body }}" | \
          jules new --repo ${{ github.repository }}
```

### 3. 정기적인 유지보수

```bash
# 매주 코드 품질 개선
cat << 'EOF' | crontab -
0 9 * * 1 cd ~/projects/querycraft && jules new "주간 코드 품질 개선: 린트 에러 수정, 타입 힌트 추가, 미사용 import 제거"
EOF
```

### 4. 배치 작업

```bash
# TODO.md의 모든 작업을 Jules에 할당
cat docs/TODO-list.md | grep "^- \[ \]" | \
  sed 's/^- \[ \] //' | \
  while IFS= read -r task; do
    jules new "$task"
    sleep 5  # API rate limit 방지
  done
```

---

## 📊 성능 벤치마크 및 비교

| 지표 | Jules | Gemini CLI | GitHub Copilot |
|------|-------|------------|----------------|
| 코딩 정확도 | **63.8%** | ~50% | ~55% |
| 비동기 실행 | ✅ | ❌ | ❌ |
| PR 자동 생성 | ✅ | ❌ | ✅ |
| 로컬 실행 | ❌ | ✅ | ✅ |
| 병렬 실행 | ✅ (최대 5개) | ❌ | ❌ |

---

## 💰 비용 및 제한

### 무료 티어
- ✅ 일일 작업 수 제한
- ✅ 기본 모델 접근
- ✅ 모든 핵심 기능

### Google AI Pro
- ✅ 더 많은 일일 작업
- ✅ Gemini 3 Pro 접근
- ✅ 우선 처리

### Google AI Ultra
- ✅ 최대 작업 수
- ✅ 고급 모델 우선 접근
- ✅ 엔터프라이즈 지원

---

## ⚡ 빠른 시작 가이드

### 1. 설치 및 로그인
```bash
npm install -g @google/jules
jules login
```

### 2. 첫 작업 생성
```bash
# 간단한 작업
jules new "README.md에 설치 가이드 추가"

# 상태 확인
jules remote list --session
```

### 3. 결과 확인 및 적용
```bash
# 세션 ID 확인 (예: 123456)
jules remote list --session

# 결과 다운로드
jules remote pull --session 123456

# 검토 후 적용
jules remote pull --session 123456 --apply
```

---

## 🎯 언제 Jules를 사용할까?

### ✅ Jules 사용이 좋은 경우
- 반복적이고 시간이 많이 걸리는 작업
- 테스트 코드 대량 생성
- 문서화 작업
- 리팩토링 (구조 개선)
- 의존성 업데이트
- 버그 수정 (명확한 재현 단계가 있을 때)

### ❌ Jules 사용이 부적합한 경우
- 즉각적인 피드백이 필요한 디버깅
- 실시간 페어 프로그래밍
- 매우 창의적이고 추상적인 설계
- 기밀성이 매우 높은 코드
- 5분 이내로 끝나는 간단한 작업

---

## 📚 추가 리소스

- **공식 사이트**: https://jules.google
- **문서**: Google AI Studio 문서
- **커뮤니티**: Reddit r/GoogleJules
- **이슈 트래커**: GitHub Issues

---

**Jules는 "유능한 주니어 개발자"를 24/7 가상으로 고용하는 것과 같습니다. 
올바르게 활용하면 개발 생산성을 크게 향상시킬 수 있습니다!** 🚀
