# 작업 분류: Claude vs Jules

## 원칙

### Claude(나)가 잘하는 것 🤖
- **설계 및 계획**: 시스템 아키텍처, API 설계, 데이터베이스 스키마
- **복잡한 로직**: 비즈니스 로직, 알고리즘, 데이터 파이프라인
- **문제 진단**: 버그 원인 분석, 성능 병목 파악
- **의사결정**: 기술 스택 선택, 아키텍처 결정
- **통합 작업**: 여러 시스템 연동, 복잡한 설정

### Jules가 잘하는 것 🚀
- **반복 작업**: 유사한 패턴의 코드 대량 생성
- **테스트 작성**: 유닛/통합 테스트 자동 생성
- **문서화**: 코드 주석, API 문서, README
- **리팩토링**: 구조 개선, 중복 제거, 코드 정리
- **보일러플레이트**: 표준 패턴 코드 생성

---

## 작업 분류

## 📋 Phase 1: 즉시 처리 (High Priority)

### 🤖 Claude가 할 일

#### 1. API 에러 진단 및 수정 방안 설계
**작업**: Leaderboard(500), Recommend(400), Translate(404) 에러 원인 파악

**이유**: 
- 복잡한 버그 진단 필요
- 비즈니스 로직 이해 필요
- 여러 시스템 연관성 파악

**우선순위**: P0 (가장 높음)

#### 2. SCHEDULER_API_KEY 설정 및 Cloud Monitoring 설정
**작업**: 헬스체크 시스템 완성

**이유**:
- GCP 설정 및 통합 작업
- 이미 90% 완료, 마무리만 필요

**우선순위**: P0

---

### 🚀 Jules에게 시킬 일

#### 1. 백엔드 전체 테스트 커버리지 80% 달성

**Jules 명령어**:
```bash
jules new "backend/ 디렉토리의 pytest 테스트 커버리지를 80%까지 높이세요.

우선순위:
1. backend/api/ - 모든 API 엔드포인트
2. backend/services/ - 핵심 비즈니스 로직
3. backend/generator/ - 데이터 생성 로직

각 모듈당 작성할 테스트:
- 정상 케이스 (200 OK, 올바른 응답)
- 인증/권한 에러 (401, 403)
- 잘못된 입력 (400)
- 서버 에러 (500)
- 엣지 케이스 (빈 데이터, null 값 등)

요구사항:
- pytest 사용
- mock을 사용하여 외부 의존성 격리
- fixtures를 활용한 테스트 데이터 관리
- 각 테스트에 명확한 docstring 추가
- pytest.ini 설정 파일 생성
- GitHub Actions CI에 테스트 자동 실행 추가

변경하지 말 것:
- 기존 코드 로직 (테스트만 추가)"
```

**예상 작업 시간**: 2-3시간
**병렬 실행**: `--parallel 3` (다양한 접근 비교)

---

#### 2. API 문서화 자동화

**Jules 명령어**:
```bash
jules new "QueryCraft API 완전 문서화:

1. README.md 업데이트:
   - 프로젝트 개요 및 주요 기능
   - 로컬 개발 환경 설정 (Docker Compose)
   - 환경 변수 전체 목록 및 설명
   - 배포 가이드 (GCP Cloud Run)
   
2. docs/API_REFERENCE.md 생성:
   - 모든 API 엔드포인트 목록
   - 각 엔드포인트별:
     * 설명
     * HTTP 메서드 및 경로
     * 요청 파라미터 (쿼리/경로/바디)
     * 요청 예시 (curl, Python requests)
     * 응답 예시 (JSON)
     * 에러 코드 및 설명
   - 인증 방법 설명
   
3. docs/CONTRIBUTING.md 생성:
   - 개발 환경 설정
   - 코드 스타일 가이드 (Python: PEP8, TypeScript: Prettier)
   - 브랜치 전략 (main, dev)
   - PR 프로세스
   - 커밋 메시지 규칙

4. backend/api/의 모든 엔드포인트에 상세한 docstring 추가:
   - Google Style Docstring 사용
   - Args, Returns, Raises 명시
   - 예시 코드 포함

출력 형식:
- Markdown 사용
- 코드 블록에 언어 지정
- 목차(TOC) 포함
- 에러 코드는 표로 정리"
```

**예상 작업 시간**: 1-2시간

---

#### 3. 프론트엔드 코드 품질 개선

**Jules 명령어**:
```bash
jules new "frontend/ 디렉토리 코드 품질 개선:

1. TypeScript 타입 안정성:
   - 모든 'any' 타입을 구체적 타입으로 변경
   - Props 인터페이스에 JSDoc 주석 추가
   - 타입 가드 함수 추가 (필요 시)
   
2. 컴포넌트 리팩토링:
   - 200줄 이상 컴포넌트를 작은 컴포넌트로 분리
   - 중복 코드를 커스텀 훅으로 추출
   - 불필요한 리렌더링 최적화 (React.memo, useMemo, useCallback)
   
3. 코드 스타일:
   - Prettier 설정 추가 (.prettierrc)
   - ESLint 규칙 강화 (.eslintrc)
   - 모든 파일에 Prettier 적용
   
4. 성능 최적화:
   - 큰 이미지 lazy loading
   - 코드 스플리팅 (React.lazy, Suspense)
   - 번들 사이즈 분석 도구 추가

변경하지 말 것:
- 기능 동작 (UI/UX는 그대로 유지)
- 파일 구조 (기존 경로 유지)"
```

**예상 작업 시간**: 2-3시간
**병렬 실행**: `--parallel 2`

---

## 📋 Phase 2: 보안 및 성능 (Medium Priority)

### 🤖 Claude가 할 일

#### 1. 데이터베이스 마이그레이션 시스템 설계
**작업**: Alembic 기반 스키마 버전 관리 설계

**이유**:
- 마이그레이션 전략 수립 필요
- 기존 데이터 보존 로직 필요
- 롤백 시나리오 설계

#### 2. RCA 시나리오 엔진 설계
**작업**: 이상 패턴 주입 알고리즘 설계 (docs/FUTURE_ROADMAP.md 참조)

**이유**:
- 비즈니스 로직 설계 필요
- 데이터 파이프라인 아키텍처 결정

---

### 🚀 Jules에게 시킬 일

#### 1. 보안 강화

**Jules 명령어**:
```bash
jules new "보안 취약점 수정:

1. 비밀번호 해싱 개선:
   - backend/api/auth.py의 SHA256을 bcrypt로 변경
   - requirements.txt에 bcrypt 추가
   - 기존 사용자 비밀번호 마이그레이션 스크립트 작성
   - 하위 호환성 유지 (기존 사용자도 로그인 가능)
   
2. SQL 인젝션 방지:
   - backend/services/에서 raw SQL 쿼리 찾기
   - 파라미터화된 쿼리로 변경
   - ORM 사용 권장 위치 주석 추가
   
3. 환경 변수 보안:
   - .env.example 파일 생성 (실제 값 없이 키만)
   - .gitignore에 .env 추가 확인
   - .env 파일 사용법 README에 추가
   
4. API 인증 강화:
   - 모든 /admin/* 엔드포인트에 is_admin 체크 추가
   - API rate limiting 미들웨어 추가
   - CORS 설정 검증

테스트:
- 각 보안 개선 항목에 대한 테스트 케이스 추가"
```

**예상 작업 시간**: 2시간

---

#### 2. 성능 최적화

**Jules 명령어**:
```bash
jules new "backend/services/grading_service.py 성능 최적화:

현재 문제:
- 108-142 라인의 DataFrame 비교 로직이 행 단위 for 루프 사용
- 대용량 데이터 처리 시 느림

개선 방법:
1. Pandas 벡터화 연산 사용:
   - for 루프를 apply(), vectorize() 등으로 변경
   - numpy 배열 연산 활용
   
2. 성능 벤치마크 추가:
   - 기존 로직 vs 개선 로직 성능 비교 스크립트
   - 다양한 데이터 크기(100, 1000, 10000행)로 테스트
   - 결과를 docs/PERFORMANCE.md에 문서화
   
3. 메모리 사용량 최적화:
   - 불필요한 DataFrame 복사 제거
   - 인덱스 활용

목표:
- 10배 이상 성능 향상
- 메모리 사용량 50% 감소

변경하지 말 것:
- 함수 시그니처
- 결과 값 (정확도 유지)"
```

**예상 작업 시간**: 1-2시간
**병렬 실행**: `--parallel 3` (여러 최적화 방법 비교)

---

## 📋 Phase 3: 신규 기능 (Lower Priority)

### 🤖 Claude가 할 일

#### 1. AI 인사이트 리포트 시스템 설계
**작업**: Gemini API 연동 아키텍처 설계

**이유**:
- 프롬프트 엔지니어링 필요
- 캐싱 전략 설계
- 비용 최적화 전략

#### 2. 개인화 추천 알고리즘 설계
**작업**: 약점 분석 및 추천 로직 설계

**이유**:
- 머신러닝 알고리즘 선택
- 데이터 파이프라인 설계
- A/B 테스트 전략

---

### 🚀 Jules에게 시킬 일

#### 1. Text-to-SQL 프로토타입

**Jules 명령어**:
```bash
jules new "Text-to-SQL 기본 기능 구현:

1. 백엔드 (backend/api/ai.py):
   - POST /api/ai/translate 엔드포인트 생성
   - 요청: { 'question': str, 'schema': dict }
   - Gemini API를 사용한 SQL 생성
   - SQL 유효성 검증 (파싱 체크)
   - 응답: { 'sql': str, 'explanation': str }
   
2. 프론트엔드:
   - src/components/TextToSQLInput.tsx 컴포넌트 생성
   - 자연어 입력 필드
   - \"SQL로 변환\" 버튼
   - 생성된 SQL을 에디터에 삽입
   - 로딩 상태 및 에러 핸들링
   
3. 프롬프트 템플릿:
   - backend/prompts/text_to_sql.txt 생성
   - 스키마 정보 포함
   - Few-shot 예제 포함
   
4. 간단한 예제로 테스트:
   - \"지난 주 가입자 수는?\"
   - \"오늘 제출한 사용자는 몇 명?\"

요구사항:
- 에러 핸들링 철저히
- API 호출 비용 로깅
- 응답 캐싱 (동일 질문)"
```

**예상 작업 시간**: 2-3시간

---

#### 2. Mixpanel 이벤트 추가

**Jules 명령어**:
```bash
jules new "Mixpanel 분석 이벤트 추가:

1. frontend/src/services/analytics.ts 확장:
   - trackTextToSQLRequested(prompt: string)
   - trackAIInsightRequested(queryResult: any)
   - trackAISuggestionApplied(suggestionType: string)
   
2. 이벤트 속성 정의:
   - prompt_length: number
   - query_complexity: 'simple' | 'medium' | 'complex'
   - ai_response_time: number
   - user_satisfaction (추후 추가 대비)
   
3. 이벤트 호출 위치:
   - TextToSQL 요청 시
   - AI 인사이트 버튼 클릭 시
   - AI 제안 적용 시
   
4. 문서화:
   - docs/ANALYTICS_GUIDE.md에 새 이벤트 추가
   - 이벤트 속성 설명
   - 분석 활용 방안

변경하지 말 것:
- 기존 이벤트 (호환성 유지)"
```

**예상 작업 시간**: 1시간

---

## 📋 Phase 4: 인프라 및 자동화

### 🤖 Claude가 할 일

#### 1. MCP 서버 설계
**작업**: Model Context Protocol 통합 아키텍처

**이유**:
- 새로운 프로토콜 통합
- 보안 및 권한 설계
- 도구(Tool) 인터페이스 설계

---

### 🚀 Jules에게 시킬 일

#### 1. CI/CD 파이프라인 개선

**Jules 명령어**:
```bash
jules new "GitHub Actions CI/CD 개선:

1. .github/workflows/test.yml 생성:
   - PR 시 자동 테스트 실행
   - pytest 커버리지 80% 미만 시 실패
   - ESLint, Prettier 검사
   - 타입 체크 (TypeScript, Python mypy)
   
2. .github/workflows/deploy.yml 개선:
   - 배포 전 테스트 필수
   - 롤백 기능 추가
   - Slack 알림 통합
   
3. 배포 스크립트:
   - scripts/deploy.sh 생성
   - 환경별 배포 (dev, staging, prod)
   - 배포 전 체크리스트 자동 실행
   
4. Docker 최적화:
   - 멀티 스테이지 빌드
   - 레이어 캐싱 최적화
   - 이미지 크기 최소화

문서화:
- docs/CICD_GUIDE.md 생성
- 배포 프로세스 상세 설명"
```

**예상 작업 시간**: 2시간

---

## 🎯 실행 우선순위

### 즉시 실행 (이번 주)
1. **Claude**: API 에러 진단 및 수정
2. **Jules**: 백엔드 테스트 커버리지 80% 달성
3. **Jules**: API 문서화

### 다음 주
4. **Jules**: 보안 강화
5. **Jules**: 성능 최적화
6. **Claude**: RCA 시나리오 엔진 설계

### 이후
7. **Jules**: Text-to-SQL 프로토타입
8. **Jules**: CI/CD 개선
9. **Claude**: MCP 서버 설계

---

## 💡 Jules 사용 팁

### 병렬 실행 전략
창의적/성능에 민감한 작업은 병렬 실행:
```bash
# 3가지 다른 최적화 방법 시도
jules new --parallel 3 "성능 최적화..."

# 완료 후 가장 좋은 결과 선택
jules remote list --session
jules remote pull --session 123456
```

### 작업 분할
큰 작업은 단계별 분할:
```bash
# Step 1
jules new "테스트 작성 Phase 1: backend/api/"
# 완료 대기
# Step 2  
jules new "테스트 작성 Phase 2: backend/services/"
```

### 결과 검토
반드시 코드 리뷰:
```bash
jules remote pull --session 123456
# 검토 후
jules remote pull --session 123456 --apply
```

---

## 📊 예상 작업량

| Phase | Claude | Jules | 총 시간 |
|-------|--------|-------|---------|
| Phase 1 | 4시간 | 6-8시간 | 10-12시간 |
| Phase 2 | 6시간 | 3-4시간 | 9-10시간 |
| Phase 3 | 8시간 | 3-4시간 | 11-12시간 |
| Phase 4 | 10시간 | 2시간 | 12시간 |
| **총합** | **28시간** | **14-18시간** | **42-46시간** |

**Jules 효과**: 약 40% 시간 단축 (반복 작업 자동화)
