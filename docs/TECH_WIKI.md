# QueryCraft Technical Wiki

> **목적**: QueryCraft의 시스템 아키텍처, 데이터 엔진, AI 기능 사양 및 인프라 운영 가이드를 총망라한 기술 라이브러리입니다. 프로젝트의 구현 세부 사항과 운영 노하우를 한곳에서 관리합니다.

---

## 🏗️ 1. Core Engine: Data & Problem Generation

QueryCraft의 핵심은 **비즈니스 시나리오 기반의 데이터 생성**과 **LLM을 활용한 문제 출제**가 결합된 아키텍처입니다.

### 1.1 Generation Pipeline

1. **Business Profiles**: 이커머스, SaaS 등 산업별 표준 지표 정의 (`product_config.py`).
2. **Synthetic Data Engine**: 확률적 사용자 행동 시뮬레이션 및 데이터 적재 (`data_generator_advanced.py`).
3. **Anomaly Injection**: 의도적인 장애 상황(이상 패턴) 주입 (`anomaly_injector.py`).
4. **Context-Aware Prompting**: 스키마와 이상 정보를 결합하여 Gemini Pro에 전달.
5. **Double-Loop Validation**: AI가 생성한 SQL을 실제 DB에서 실행 검증 후 문제 확정.

### 1.2 통합 Generator 아키텍처 (2026-01-19 구축)

**단일 엔트리 포인트**를 통해 PA, Stream, RCA 모든 문제 타입을 생성하는 통합 아키텍처입니다.

**호출 인터페이스**:
```python
from problems.generator import generate

# PA: 2세트(12문제) 생성
generate(today, pg, mode="pa")

# Stream: 1세트(6문제) 생성
generate(today, pg, mode="stream")

# RCA: 1세트(6문제) 생성
generate(today, pg, mode="rca")
```

**내부 흐름**:
1. `prompt.py::build_prompt(mode)` 호출 → mode별 프롬프트 자동 선택
   - `mode="pa"` → `build_pa_prompt()`
   - `mode="stream"` → `build_stream_prompt()` (새로 추가)
   - `mode="rca"` → `build_rca_prompt()`
2. Gemini API 호출하여 6개 문제 생성
3. 각 문제의 answer_sql 실행하여 expected_result 생성
4. **PostgreSQL DB 저장 (Primary Source)**
5. 파일 저장 (백업/로컬 개발용, 실패해도 중단하지 않음)

**안정성 강화**:
- **Cloud Run 대응**: `K_SERVICE` 환경 변수로 Cloud Run 감지, DB-first 모드
- **Graceful Degradation**: 파일 저장 실패 시 warning 처리, 데이터 손실 방지
- **에러 원천 차단**: `ensure_dir()`, `safe_save_json()` 헬퍼 함수로 파일 시스템 에러 방지

### 1.3 핵심 기술 파일

| 파일 | 역할 | 특징 |
| :--- | :--- | :--- |
| `problems/generator.py` | **통합 문제 생성기** | PA/Stream/RCA 단일 인터페이스, mode별 동적 세트 수 결정 |
| `problems/prompt.py` | 프롬프트 라우터 | mode별 프롬프트 자동 선택 및 Gemini 호출 |
| `problems/prompt_stream.py` | Stream 프롬프트 | Stream 데이터 요약 및 프롬프트 생성 (2026-01-19 신규) |
| `data_generator_advanced.py` | 대량 데이터 생성 | `COPY` 명령어를 통한 고속 적재 지원 |
| `anomaly_injector.py` | 시나리오 설계 | RCA 모드를 위한 구체적인 장애 도메인 주입 |

> [!TIP]
> **Generator 상세 가이드**: 구현 예시와 검증 규칙은 [**GENERATOR_GUIDE.md**](./GENERATOR_GUIDE.md)를 참조하세요.

---

## 🤖 2. Future Lab AI 기능 사양

AI 기능을 통해 분석가에게 진화된 업무 환경을 제공합니다.

### 2.1 RCA (Root Cause Analysis) 시나리오

- **컨셉**: 매출 급감 등 비즈니스 위기 상황을 SQL로 해결하는 시뮬레이션.
- **AI 역할**: 매일 새로운 원인이 담긴 데이터 주입 및 단계별 힌트 생성.
- **구현**: 사용자가 제출한 SQL과 답변 내용을 AI가 논리적/정량적으로 동시 평가.

### 2.2 Text-to-SQL & AI Insight

- **Text-to-SQL**: 자연어 질문을 에디터 내에서 즉시 SQL 초안으로 변환.
- **AI Insight**: 쿼리 결과 테이블을 분석하여 **Key Findings**, **Action Items**를 도출하는 리포트 자동 생성.

### 2.3 MCP (Model Context Protocol) 연동

- **목표**: 외부 IDE(Cursor, Claude Desktop)가 QueryCraft의 DB 스키마와 문제 데이터에 직접 접근.
- **Tool 스펙**: `get_schema`, `preview_data`, `execute_sql`, `submit_solution` 등 제공.

---

## 🎨 3. Design System (Design Tokens)

QueryCraft의 프론트엔드는 디자인 일관성과 유지보수를 위해 **Design Tokens** 시스템을 사용합니다. 모든 시각적 요소는 하드코딩된 값 대신 토큰화된 변수를 참조합니다.

### 3.1 토큰 카테고리

- **Colors**: 브랜드 컬러 및 시맨틱 컬러(Success, Error 등) 정의. 다크/라이트 모드 대응 지원.
- **Spacing**: 4px 베이스 유닛 기반의 `var(--space-*)` 활용.
- **Typography**: 폰트 크기, 굵기, 자간을 관리하여 타이포그래피 일관성 유지.
- **Radius/Breakpoints**: 컴포넌트 라운딩 및 반응형 레이아웃 토큰.

### 3.2 사용 규칙

- **항상 토큰 사용**: CSS 작성 시 픽셀(`px`)이나 색상 코드(`#`)를 직접 사용하는 대신 `var(--token-name)`을 사용합니다.
- **시맨틱 컬러 우선**: 특정 색상(예: `--neon-green`)보다 목적에 맞는 토큰(예: `--success-color`)을 우선 사용합니다.
- **상세 명세**: [DESIGN_TOKENS_GUIDE.md](./DESIGN_TOKENS_GUIDE.md)
- **컴포넌트 라이브러리**: Arcade UI Primitives의 상세 Props와 사용 예시는 [**UI_COMPONENTS_GUIDE.md**](./UI_COMPONENTS_GUIDE.md)를 참조하세요.

---

## 🚀 4. 인프라 배포 및 운영 가이드

### 4.1 상용 아키텍처 (GCP + Supabase)

- **Frontend/Backend**: GCP Cloud Run (Docker 기반 서버리스).
- **Database**: Supabase (PostgreSQL 15+).
- **Scheduler**: GCP Cloud Scheduler → Cloud Run Worker 직접 트리거.
- **CI/CD**: GitHub Actions를 통한 `main` 브랜치 자동 배포.

### 4.2 필수 환경 변수

- **POSTGRES_DSN**: Supabase 연결 URI. `postgresql://user:pass@host:port/dbname?sslmode=require` 형식을 권장합니다. (공백 구분자 형식은 일부 모듈에서 파싱 오류를 발생시킬 수 있음)
- **GEMINI_API_KEY**: Google Gemini Pro API Key.
- **ENV**: `production` 또는 `development`.

### 4.3 운영 노하우

- **KST 보정**: 모든 날짜 계산은 `backend/common/date_utils.py`를 통해 한국 시간으로 처리.
- **백필(Backfill)**: `worker/main.py --date YYYY-MM-DD` 인자를 통해 누락된 과거 데이터 생성 가능.

---

## 📊 5. 분석 설계 (Analytics Implementation)

### 5.1 Analytics Stack

- **Mixpanel**: 주력 유저 행동 분석 (퍼널, 리텐션, 코호트).
- **GA4**: 서비스 유입 및 기본 지표 모니터링.

### 5.2 핵심 트래킹 이벤트

#### 데이터 명명 규칙

- **Event**: Title Case (예: `Problem Solved`).
- **Property**: Snake Case (예: `attempt_count`).

---

## 📂 6. 기술 의사결정 기록 (Archived Plans)

*과거 주요 시스템 변경 사항 및 구현 계획 아카이브입니다.*

- **Cloud Scheduler 개선**: 백엔드 호출 방식에서 Cloud Run Job 직접 트리거 방식으로 변경하여 안정성 확보.
- **RCA 고도화**: 단순 에러 주입을 넘어 비즈니스 맥락(Retention Drop 등)이 포함된 시나리오 엔진 구축.
- **로그인 시스템 안정성**: `login_attempts` 테이블을 통한 무차별 대입 공격 방어(Rate Limiting) 적용.

---

---

## 🛡️ 7. Operational Stability & Recovery (운영 안정성)

서비스의 지속 가능성을 위해 문제 생성 및 채점 파이프라인에는 다중 방어 기제가 적용되어 있습니다.

### 7.1 404 에러 방어 (Defense-in-Depth)
- **ID 기반 검색**: 채점 시 `target_date`에 종속되지 않고 `problem_id`로만 직접 검색하도록 개선하여, 서버간 시간차나 세션 만료로 인한 404를 방지합니다.
- **Lazy Schema Discovery**: 테이블 스키마 조회 시 캐싱 대신 실시간 메타데이터를 참조하여 데이터 생성 직후 즉시 채점이 가능하도록 합니다.

### 7.2 자가 복구 메커니즘 (Self-Healing)
- **Emergency Fallback**: AI(Gemini) 오류로 당일 문제 생성에 실패할 경우, 시스템은 자동으로 **가장 최근 성공한 챌린지를 오늘 날짜로 복제**하여 서비스 중단을 막습니다.
- **Health-check Trigger**: `/health/daily-problems` 호출 시 데이터 부재를 감지하면 즉시 백그라운드 생성을 시도합니다.

### 7.3 운영진을 위한 골든 룰
1. **모니터링**: 아침 9시 이후 서비스 접속 시 문제가 없다면 성공입니다.
2. **수동 복구**: 404 발생 시 관리자 페이지의 **[통합 생성]** 버튼을 누르거나 `health-check` 엔드포인트를 호출하세요.
3. **환경 변수**: `POSTGRES_DSN`은 반드시 **URI 형식**을 유지해야 합니다.

---

## 8. Core Stability Guardrails (핵심 기능 고정)

사용자 경험의 핵심인 에디터, 문제 로드, 채점 프로세스는 현재 "Golden State"로 간주되어 고정(Freeze)되었습니다.

### 7.1 보호 대상 및 지침
- **대상**: `SQLEditor.tsx`, `grading_service.py`, `problem_service.py`, `sql.py`, `postgres_engine.py`.
- **지침**: 해당 파일들의 핵심 로직을 변경해야 할 경우, 반드시 사용자에게 변경 사유와 영향을 명시적으로 보고하고 승인을 얻어야 합니다. 단순 리팩토링이나 구조적 변경보다는 안정성을 우선시합니다.

---

**마지막 업데이트: 2026-01-30 (운영 안정성 패치 적용)**
