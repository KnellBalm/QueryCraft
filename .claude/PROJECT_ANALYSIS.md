# QueryCraft 프로젝트 분석 리포트

생성일: 2026-01-15

## 코드 규모

| 영역 | 라인 수 | 평가 |
|------|---------|------|
| Backend | 6,946 | 적정 |
| Frontend | 4,654 | 적정 |
| Tests | 261 | 너무 적음 (~3.7%) |

---

## Critical Issues (즉시 해결 필요)

### 1. .env 파일에 API 키 노출
- **파일**: `.env`
- **노출된 키**: `GEMINI_API_KEY`, `GOOGLE_CLIENT_SECRET`, `SMTP_PASSWORD`
- **조치**: 즉시 키 재발급, `.env.example` 분리

### 2. 취약한 비밀번호 해싱
- **파일**: `backend/api/auth.py:162-176`
- **문제**: SHA256 사용 (보안에 취약)
```python
def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    hashed = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}:{hashed}"
```
- **조치**: `bcrypt` 또는 `argon2`로 변경

### 3. SQL Injection 방어 미흡
- **파일**: `backend/services/sql_service.py:17-30`
- **문제**: Blacklist 방식 (우회 가능)
- **조치**: Allowlist 방식으로 변경 (SELECT만 허용)

---

## High Priority Issues

### 4. 테스트 커버리지 부족 ✅ (일부 완료)
- **현재**: 테스트:코드 비율 1:26
- **권장**: 1:5 이상
- **추가된 테스트**:
  - ✅ Auth 엔드포인트 테스트 (`tests/test_auth.py`)
  - ✅ Grading 엣지케이스 테스트 (날짜 처리, NULL 비교 등)
- **아직 필요**:
  - Frontend 컴포넌트 테스트
- **파일**: `tests/` 디렉토리

### 5. 성능 병목 - DataFrame 비교 ✅ (완료)
- **파일**: `backend/services/grading_service.py:107-166`
- **해결**: Pandas 벡터화 연산으로 변경 완료
  - 컬럼 단위 벡터화 비교
  - NULL 비교 벡터화
  - 숫자/문자열/날짜 비교 최적화

### 6. Docker 보안 문제 ✅ (완료)
- **파일**: `backend/Dockerfile`, `docker-compose.dev.yml`
- **해결됨**:
  - ✅ Non-root 사용자로 실행 (appuser:appgroup)
  - ✅ Health check 추가
  - ✅ 리소스 제한 추가 (CPU, Memory limits)

---

## Medium Priority Issues

### 7. 로깅 일관성 부족
- **문제**: `print()` 10곳에서 사용
- **위치**:
  - `backend/services/problem_service.py:83`
  - 기타 서비스 파일들
- **조치**: `logger.info()`로 통일

### 8. TypeScript 타입 안전성
- **파일**: `frontend/src/components/SQLEditor.tsx:52-55`
```typescript
// @ts-ignore - window 전역 플래그로 중복 등록 방지
if (!window.__sqlCompletionRegistered) {
    // @ts-ignore
    window.__sqlCompletionRegistered = true;
}
```
- **조치**: Window 인터페이스 확장

### 9. 환경변수 검증 없음
- **파일**: `backend/config/settings.py`
- **문제**: 필수 변수 시작 시 검증 안 함 (`PG_HOST`, `DUCKDB_PATH`)
- **조치**: 앱 시작 시 필수 환경변수 검증 추가

### 10. 데이터 소스 혼재
- **파일**: `backend/services/problem_service.py:68-90`
- **문제**: 문제 데이터가 DB와 파일 시스템에 병행 저장
- **조치**: 단일 소스 정책 수립

### 11. 세션 보안
- **파일**: `backend/api/auth.py:39-56`
```python
response.set_cookie(
    "session_id", session_id,
    max_age=86400*7,  # 7일은 너무 김
    samesite='none' if is_prod else 'lax'  # CSRF 위험
)
```

### 12. CORS 설정
- **파일**: `backend/main.py:88-111`
- **문제**: 하드코딩된 IP (`192.168.101.224`), 너무 넓은 와일드카드

---

## Low Priority Issues

### 13. 코드 품질
- Magic numbers 사용 (`backend/api/auth.py:185` - 비밀번호 길이 4)
- 함수 인자 변경 (`grading_service.py:86-89` - DataFrame 직접 수정)
- 제네릭 에러 메시지 (사용자에게 "오류 발생"만 표시)

### 14. 문서화 부족
- ADR (Architecture Decision Records) 없음
- 배포 가이드 없음
- API 에러 코드 문서 없음

---

## 잘 된 부분

| 항목 | 설명 |
|------|------|
| 프로젝트 구조 | Backend/Frontend 분리, 서비스 레이어 명확 |
| API 설계 | RESTful 패턴 준수, Pydantic 검증 |
| DB 전략 | PostgreSQL(메타) + DuckDB(분석) 하이브리드 |
| TypeScript | 인터페이스 정의, 타입 힌트 사용 |
| FastAPI 문서 | OpenAPI 자동 생성 (`/docs`) |
| Context 관리 | Auth, Theme, Track Context 적절히 분리 |

---

## 권장 작업 순서

### Phase 1: 보안 (즉시)
1. API 키 재발급 및 .env.example 분리
2. bcrypt로 비밀번호 해싱 변경
3. SQL allowlist 방식 변경
4. OAuth state 파라미터 검증 추가

### Phase 2: 품질 (단기) ✅ (일부 완료)
1. ✅ Auth, Grading 테스트 추가 - `tests/test_auth.py` 신규 작성, `tests/test_grader.py` 11개 테스트 추가
2. ✅ DataFrame 비교 벡터화 - `grading_service.py` 벡터화 완료
3. print() → logger 통일
4. 환경변수 시작 시 검증

### Phase 3: 아키텍처 (중기)
1. Redis 캐싱 도입 (문제 답안)
2. Rate limiting 미들웨어 추가
3. API 에러 코드 문서화
4. 구조화된 로깅 (JSON 포맷)

### Phase 4: 운영 (장기) ✅ (일부 완료)
1. ✅ Docker health check 및 리소스 제한 - `backend/Dockerfile`, `docker-compose.dev.yml` 완료
2. 배포 절차 문서화
3. ADR 작성
4. CI/CD에 보안 스캐닝 추가

---

## 주요 파일 위치 요약

| 카테고리 | 파일 |
|----------|------|
| 비밀번호 해싱 | `backend/api/auth.py:162-176` |
| SQL 검증 | `backend/services/sql_service.py:17-30` |
| 채점 로직 | `backend/services/grading_service.py:108-142` |
| 문제 서비스 | `backend/services/problem_service.py` |
| 설정 | `backend/config/settings.py` |
| Docker | `Dockerfile`, `docker-compose.yml`, `docker-compose.dev.yml` |
| 테스트 | `tests/test_grader.py`, `tests/test_duckdb_engine.py`, `tests/test_auth.py` |
| 프론트 에디터 | `frontend/src/components/SQLEditor.tsx` |
| 환경변수 | `.env`, `.env.dev` |
