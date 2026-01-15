# TODO List

> 📅 마지막 업데이트: 2026-01-16 (GNB & 서비스 구축 완료)

---

### Mixpanel 분석
- [ ] 대시보드 설정 (Funnel, Retention, Flow)
- [x] AI 사용 임계치 이벤트 트래킹 추가

> 📎 상세 설계: `docs/IMPLEMENTATION_PLAN.md`


---

## 1. 백엔드 API 에러 해결 마무리

### 1.1 API 동작 검증 (P0)
- [ ] Leaderboard API (500 에러) 해결 확인
  - [ ] 에러 원인 파악 (로그 확인)
  - [ ] 수정 후 로컬 테스트
  - [ ] dev 서버 배포 후 검증
- [ ] Recommend API (400 에러) 해결 확인
  - [ ] 요청 파라미터 검증 로직 확인
  - [ ] 수정 후 테스트
- [ ] Translate API (404 에러) 해결 확인
  - [ ] 라우트 등록 여부 확인
  - [ ] 엔드포인트 경로 검증

### 1.2 배포
- [ ] `dev` 브랜치 소스 푸시 (검증 완료 후)

---

## 2. 스케줄러 개선 (Cloud Run 연동)

### 2.1 전용 스케줄 엔드포인트 설계
- [ ] 엔드포인트 경로 결정: `/admin/schedule/run`
- [ ] 요청/응답 스키마 정의
  ```json
  // 응답 예시
  {
    "status": "success",
    "data_generated": true,
    "problems_generated": 3,
    "duration_sec": 45.2
  }
  ```

### 2.2 엔드포인트 구현
- [ ] `backend/api/admin.py`에 엔드포인트 추가
- [ ] 데이터 생성 + 문제 생성 로직 호출
- [ ] 예외 처리 및 에러 응답 정의

### 2.3 인증 및 보안
- [ ] 인증 방식 결정 (OIDC 토큰 vs API 키)
- [ ] `X-Scheduler-Key` 헤더 검증 로직 구현
- [ ] 서비스 계정 전용 Cloud Run Invoker 권한 설정

### 2.4 내부 스케줄러 정리
- [ ] `ENABLE_SCHEDULER` 환경변수로 내부 스케줄러 비활성화 옵션 추가
- [ ] 중복 실행 방지 플래그 추가 (락 메커니즘)

---

## 3. Cloud Scheduler 설정 (GCP)

### 3.1 Scheduler 생성
- [ ] 이름: `querycraft-daily-generation`
- [ ] Cron 표현식: `0 1 * * *`
- [ ] 타임존: `Asia/Seoul`
- [ ] 대상 URL: `https://[CLOUD_RUN_URL]/admin/schedule/run`

### 3.2 서비스 계정 설정
- [ ] 서비스 계정 생성: `querycraft-scheduler-sa`
- [ ] Cloud Run Invoker 역할 부여
- [ ] Scheduler에 서비스 계정 연결

### 3.3 재시도 및 알림 설정
- [ ] 재시도 정책: 최대 3회, 지수 백오프
- [ ] 실패 알림 설정
  - [ ] Cloud Logging 알림 규칙 생성
  - [ ] (선택) Slack/이메일 연동

---

## 4. 배포/운영 점검

- [ ] 환경변수 정리
  - [ ] `ENV=production` 설정 확인
  - [ ] `ENABLE_SCHEDULER=false` (Cloud Scheduler 사용 시)
- [ ] 스케줄러 중복 실행 모니터링 대시보드 구성
- [ ] 생성 결과 검증 스크립트 작성
  - [ ] `problems/daily/` 파일 존재 확인
  - [ ] DB에 오늘 날짜 문제 데이터 확인

---

## 5. MixPanel 이벤트 추가 및 개선

### 5.1 신규 이벤트 정의
- [ ] AI Lab 이벤트 추가
  - [ ] `Text to SQL Requested` (자연어→SQL 변환 요청)
  - [ ] `AI Insight Requested` (결과 인사이트 요청)
  - [ ] `AI Suggestion Applied` (AI 제안 적용)
- [ ] 속성 정의: `prompt_version`, `experiment_group`

### 5.2 구현
- [ ] `frontend/src/services/analytics.ts` 이벤트 메서드 추가
- [ ] 해당 컴포넌트에서 이벤트 호출 연결
- [ ] 스테이징/프로덕션 토큰 분리 확인

### 5.3 검증 및 문서화
- [ ] Mixpanel Live View에서 이벤트 수집 확인
- [ ] `docs/ANALYTICS_GUIDE.md` 이벤트 목록 업데이트

---

## 6. RCA 시나리오 모드 고도화

### 6.1 시나리오 다양화
- [ ] 새로운 장애 시나리오 템플릿 추가
  - [ ] "리텐션 급락" 시나리오
  - [ ] "특정 채널 효율 저하" 시나리오
  - [ ] "가입 전환율 하락" 시나리오
- [ ] 시나리오별 데이터 패턴 정의

### 6.2 UI/UX 개선
- [ ] RCA 모드 전용 대시보드 레이아웃
- [ ] 단계별 힌트 시스템 강화
- [ ] 분석 결과 리포트 템플릿 제공

---

## 7. AI 인사이트 리포트 자동화 (신규)

### 7.1 기능 설계
- [ ] SQL 결과 → AI 분석 파이프라인 설계
- [ ] 인사이트 리포트 출력 형식 정의
  - [ ] 핵심 발견 (Key Findings)
  - [ ] 추천 액션 (Action Items)
  - [ ] 추가 분석 제안

### 7.2 백엔드 구현
- [ ] `/api/ai/insight` 엔드포인트 설계
- [ ] Gemini API 연동 (결과 데이터 → 인사이트 생성)
- [ ] 응답 캐싱 (동일 쿼리 결과에 대해)

### 7.3 프론트엔드 구현
- [ ] AI 인사이트 패널 컴포넌트 개발
- [ ] 결과 테이블 옆 "인사이트 보기" 버튼 추가
- [ ] 로딩 상태 및 에러 핸들링

---

## 8. 개인화 학습 추천 (Adaptive Learning) (신규)

### 8.1 데이터 수집
- [ ] 사용자별 풀이 기록 분석 테이블 설계
  - [ ] 오답 문제 ID, 풀이 시간, SQL 패턴
- [ ] 약점 분석 알고리즘 설계

### 8.2 추천 엔진
- [ ] 약점 기반 문제 추천 로직 구현
- [ ] 난이도 점진적 상승 알고리즘
- [ ] `/api/recommend` 엔드포인트 개선

### 8.3 프론트엔드
- [ ] "맞춤 추천" 섹션 UI 개발
- [ ] 추천 이유 표시 ("조인 문제에서 어려움을 겪고 계시네요")

---

## 9. Text-to-SQL 보조 도구 (신규)

### 9.1 기능 설계
- [ ] 자연어 입력 → SQL 초안 생성 플로우
- [ ] 스키마 컨텍스트 주입 방식 결정

### 9.2 백엔드 구현
- [ ] `/api/ai/translate` 엔드포인트 설계
- [ ] 스키마 정보 + 자연어 → Gemini Pro 프롬프트
- [ ] 생성된 SQL 유효성 검증

### 9.3 프론트엔드 구현
- [ ] SQL 에디터 상단 자연어 입력 필드
- [ ] "SQL로 변환" 버튼 및 결과 삽입 기능

---

## 10. MCP (Model Context Protocol) 연동 (신규)

### 10.1 Phase 1: 기본 인프라
- [ ] `mcp-python-sdk` 설치 및 설정
- [ ] 기본 DB 조회 도구 구현
  - [ ] `get_schema(table_name)`: 테이블 스키마 조회
  - [ ] `preview_data(table_name, limit)`: 샘플 데이터 조회
  - [ ] `check_query_plan(sql)`: 실행 계획 분석

### 10.2 Phase 2: AI 힌트 연동
- [ ] 힌트 시스템에 MCP 도구 연동
- [ ] "실제 데이터를 확인해보니..." 형태의 힌트 제공
- [ ] 쿼리 실행 전 데이터 존재 여부 확인

### 10.3 Phase 3: 관리자 에이전트
- [ ] 관리자용 MCP 서버 구축
  - [ ] `get_daily_active_users()`: DAU 조회
  - [ ] `get_problem_pass_rate(problem_id)`: 문제별 정답률
- [ ] 자연어로 서비스 지표 조회 기능

### 10.4 Phase 4: 외부 IDE 연동
- [ ] MCP 리소스 노출
  - [ ] `problems/today`: 오늘의 문제
  - [ ] `schema/all`: 전체 스키마
- [ ] Cursor IDE / Claude Desktop 연동 테스트
