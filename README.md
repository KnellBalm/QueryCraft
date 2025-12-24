# SQL Analytics Lab

> 프로덕트 분석가 양성을 위한 AI 기반 SQL 실습 플랫폼

---

## Table of Contents

### Quick Navigation

| Overview | For Planners | For Developers | For Analysts |
|:--------:|:------------:|:--------------:|:------------:|
| [Introduction](#1-introduction) | [Product Specification](#6-product-specification) | [Development Guide](#7-development-guide) | [Analysis Guide](#8-analysis-guide) |
| [Features](#2-features) | [User Journey](#65-user-journey-map) | [Local Setup](#73-local-development) | [Data Schema](#84-data-schema) |
| [Quick Start](#5-quick-start) | [KPI Definition](#66-kpi-definition) | [Architecture](#74-system-architecture) | [Problem Types](#83-problem-categories) |

### Full Index

1. [Introduction](#1-introduction)
2. [Features](#2-features)
3. [System Architecture](#3-system-architecture)
4. [Tech Stack](#4-tech-stack)
5. [Quick Start](#5-quick-start)
6. [Product Specification](#6-product-specification)
7. [Development Guide](#7-development-guide)
8. [Analysis Guide](#8-analysis-guide)
9. [Documentation](#9-documentation)
10. [Roadmap](#10-roadmap)

---

## 1. Introduction

### 1.1 Problem Statement

| Pain Point | Solution |
|------------|----------|
| 교과서적 SQL 문법 학습만 가능 | 실무 비즈니스 질문 기반 문제 |
| 단순 SELECT 쿼리 연습 | 퍼널/코호트/리텐션 분석 |
| 정답 확인만 가능 | AI 기반 피드백 및 개선 제안 |
| 단일 도메인 데이터셋 | 5가지 프로덕트 타입 지원 |

### 1.2 Target Users

| Segment | Needs | Expected Outcome |
|---------|-------|------------------|
| 취업 준비생 | 실무 경험 대체, 포트폴리오 | 면접 준비, 과제 수행 역량 |
| 주니어 분석가 | 분석 프레임워크 학습 | 시니어 레벨 역량 획득 |
| PM/기획자 | 데이터 기반 의사결정 | 직접 쿼리 작성 능력 |

### 1.3 Value Proposition

- **6가지 분석 유형** 마스터 → 어떤 도메인에서든 분석 업무 수행
- **AI 피드백** 활용 → 시니어 분석가 코드리뷰 효과
- **실제 데이터 패턴** 경험 → 면접/과제에 즉시 적용 가능

---

## 2. Features

### 2.1 Core Features

| Feature | Description | Priority |
|---------|-------------|----------|
| PA Problem Solving | 정적 분석 문제 6개/일 | P0 |
| Stream Problem Solving | 동적 로그 분석 문제 | P0 |
| SQL Editor | Monaco 기반 인터랙티브 에디터 | P0 |
| Auto Grading | 결과 테이블 비교 기반 채점 | P0 |
| AI Feedback | Gemini 기반 코드 리뷰 | P1 |
| Schema Explorer | 테이블/컬럼 정보 조회 | P1 |

### 2.2 Supported Product Types

| Type | Domain | Events | Analysis Focus |
|------|--------|--------|----------------|
| Commerce | E-commerce | 15 | Funnel, Cart Abandonment |
| Content | Media Platform | 12 | Read-through Rate, Subscription |
| SaaS | B2B Software | 13 | Activation, Feature Adoption |
| Community | Social Network | 11 | Creator/Consumer Ratio |
| Fintech | Financial Service | 12 | Transaction Success Rate, KYC |

---

## 3. System Architecture

### 3.1 High-Level Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Client Layer                               │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                    React SPA (Vite)                           │  │
│  │                       :5173                                   │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │ REST API
┌─────────────────────────────────▼───────────────────────────────────┐
│                          Service Layer                              │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                    FastAPI Backend                            │  │
│  │                       :8000                                   │  │
│  └───────────────────────────────────────────────────────────────┘  │
└───────────┬─────────────────────┬─────────────────────┬─────────────┘
            │                     │                     │
┌───────────▼───────────┐ ┌───────▼───────┐ ┌───────────▼───────────┐
│     PostgreSQL        │ │    DuckDB     │ │     Gemini API        │
│    (Primary DB)       │ │ (Analytics)   │ │    (AI Feedback)      │
└───────────────────────┘ └───────────────┘ └───────────────────────┘
            │
┌───────────▼───────────────────────────────────────────────────────┐
│                         Scheduler                                  │
│               (Automated Data & Problem Generation)                │
└───────────────────────────────────────────────────────────────────┘
```

### 3.2 Data Generation Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│ Phase 1: Product Type Selection                                     │
├─────────────────────────────────────────────────────────────────────┤
│   commerce    content     saas      community    fintech           │
│     20%        20%        20%         20%         20%              │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Phase 2: Event Generation (Strategy Pattern)                       │
├─────────────────────────────────────────────────────────────────────┤
│   BaseProductProfile                                                │
│         │                                                           │
│         ├── CommerceProfile.generate_session_events()               │
│         ├── ContentProfile.generate_session_events()                │
│         ├── SaaSProfile.generate_session_events()                   │
│         ├── CommunityProfile.generate_session_events()              │
│         └── FintechProfile.generate_session_events()                │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Phase 3: Data Persistence                                           │
├─────────────────────────────────────────────────────────────────────┤
│   PostgreSQL: pa_users, pa_sessions, pa_events, pa_orders           │
│   DuckDB: stream_events, stream_daily_metrics                       │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Phase 4: Problem Generation (Gemini AI)                             │
├─────────────────────────────────────────────────────────────────────┤
│   Product Type → Customized Prompt → 6 Problems / Day              │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.3 Design Patterns

| Pattern | Application | Benefit |
|---------|-------------|---------|
| Strategy | ProductProfile | 타입별 이벤트 생성 로직 분리 |
| Factory | get_profile() | 문자열 기반 인스턴스 생성 |
| Repository | Engine Classes | DB 접근 추상화 |
| Service Layer | Generator, Grader | 비즈니스 로직 캡슐화 |

---

## 4. Tech Stack

### 4.1 Frontend

| Technology | Version | Purpose |
|------------|---------|---------|
| React | 18.x | UI Framework |
| Vite | 5.x | Build Tool |
| TypeScript | 5.x | Type Safety |
| Monaco Editor | - | SQL Code Editor |
| Mixpanel | - | Event Tracking |
| PostHog | - | Analytics & Session Recording |

### 4.2 Backend

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.12+ | Runtime |
| FastAPI | 0.115+ | API Server |
| Pydantic | 2.x | Data Validation |
| Pandas | - | Data Processing |
| psycopg2 | - | PostgreSQL Driver |
| DuckDB | - | Analytics Database |

### 4.3 AI & Analytics

| Technology | Purpose |
|------------|---------|
| Google Gemini Pro | Problem Generation, AI Feedback |
| Mixpanel | User Behavior Analytics |
| PostHog | Event Tracking, Session Recording |

### 4.4 Infrastructure

| Technology | Purpose |
|------------|---------|
| Docker Compose | Container Orchestration |
| PostgreSQL | Primary Database |
| DuckDB | Analytics Database |

---

## 5. Quick Start

### 5.1 Prerequisites

```bash
# Required
- Docker & Docker Compose
- Git

# Optional (Local Development)
- Node.js 18+
- Python 3.12+
```

### 5.2 Installation

```bash
# Clone Repository
git clone https://github.com/your-org/offline_lab.git
cd offline_lab

# Configure Environment
cp .env.example .env
# Edit .env file (Gemini API Key, etc.)

# Start Services
docker compose up -d

# Access
# Frontend: http://localhost:5173
# API Docs: http://localhost:8000/docs
# Admin: http://localhost:5173/admin
```

### 5.3 Initial Data Setup

```bash
docker compose exec backend python -c "
from generator.data_generator_advanced import run_pa
from problems.generator import generate as gen_pa
from engine.postgres_engine import PostgresEngine
from config.db import PostgresEnv
from datetime import date

run_pa()
pg = PostgresEngine(PostgresEnv().dsn())
gen_pa(date.today(), pg)
pg.close()
"
```

---

## 6. Product Specification

### 6.1 Service Concept

> PM/마케팅팀에서 슬랙으로 데이터 분석을 요청하는 실무 상황 시뮬레이션

**UX Principles:**
1. 실무 톤앤매너: "PM팀입니다. ~분석 부탁드려요" 형식
2. 명확한 요구사항: 필요 컬럼, 정렬 기준, 기간 명시
3. 즉각적 피드백: 실행 결과 즉시 확인
4. AI 리뷰: 시니어 분석가 관점 개선점 제안

### 6.2 Feature Matrix

#### User Features

| Feature | Description | Status |
|---------|-------------|--------|
| PA Problem Solving | 정적 분석 문제 6개/일 | ✅ |
| Stream Problem Solving | 동적 로그 분석 문제 | ✅ |
| SQL Editor | Monaco 기반 코드 작성 | ✅ |
| Auto Grading | 결과 테이블 비교 채점 | ✅ |
| AI Feedback | Gemini 기반 코드 리뷰 | ✅ |
| Schema Explorer | 테이블/컬럼 정보 조회 | ✅ |
| Submission History | 제출 이력 관리 | ✅ |

#### Admin Features

| Feature | Description | Status |
|---------|-------------|--------|
| Problem Generation | PA/Stream 문제 수동 생성 | ✅ |
| Data Refresh | 사용자/이벤트 데이터 재생성 | ✅ |
| Scheduler Monitoring | 자동 생성 로그 확인 | ✅ |
| Dataset Version Control | 생성 이력 조회 | ✅ |

### 6.3 Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-001 | 사용자는 6개의 PA 문제를 조회할 수 있다 | P0 |
| FR-002 | 사용자는 SQL을 작성하고 실행할 수 있다 | P0 |
| FR-003 | 사용자는 정답을 제출하고 채점 결과를 확인할 수 있다 | P0 |
| FR-004 | 사용자는 AI 피드백을 요청할 수 있다 | P1 |
| FR-005 | 관리자는 문제를 수동으로 생성할 수 있다 | P1 |
| FR-006 | 시스템은 매일 자동으로 새 문제를 생성한다 | P1 |

### 6.4 Non-Functional Requirements

| ID | Requirement | Metric |
|----|-------------|--------|
| NFR-001 | API 응답 시간 | < 500ms (p95) |
| NFR-002 | SQL 실행 시간 | < 5s (타임아웃) |
| NFR-003 | AI 피드백 응답 시간 | < 30s |
| NFR-004 | 동시 사용자 지원 | 100명 |

### 6.5 User Journey Map

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│  Visit   │──▶│  Select  │──▶│  Write   │──▶│  Submit  │──▶│ Feedback │
│          │   │  Problem │   │   SQL    │   │          │   │          │
└──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘
                    │              │              │              │
                    ▼              ▼              ▼              ▼
              ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
              │  Schema  │  │  Execute │  │   Auto   │  │    AI    │
              │  Lookup  │  │  Preview │  │  Grading │  │  Review  │
              └──────────┘  └──────────┘  └──────────┘  └──────────┘
```

### 6.6 KPI Definition

| Metric | Definition | Target |
|--------|------------|--------|
| DAU | Daily Active Users | - |
| Problem Completion Rate | Submissions / Views | > 40% |
| Accuracy Rate | Correct / Total Submissions | > 60% |
| Problems per Session | Average attempts | > 2 |
| D1 Retention | Next-day return rate | > 30% |

---

## 7. Development Guide

### 7.1 Project Structure

```
offline_lab/
├── backend/                    # FastAPI Backend
│   ├── api/                    # API Routers
│   │   ├── admin.py            # Admin API
│   │   ├── problems.py         # Problem API
│   │   └── stats.py            # Statistics API
│   ├── schemas/                # Pydantic Schemas
│   └── main.py                 # FastAPI App
│
├── frontend/                   # React Frontend
│   ├── src/
│   │   ├── pages/              # Page Components
│   │   ├── components/         # Shared Components
│   │   ├── services/           # API Client, Analytics
│   │   └── App.tsx             # Routing
│   └── index.html              # Entry Point
│
├── generator/                  # Data Generator
│   ├── product_config.py       # Product Type Config
│   ├── product_profiles/       # Strategy Profiles
│   │   ├── base.py             # Base Class
│   │   ├── commerce.py         # E-commerce Profile
│   │   ├── content.py          # Content Profile
│   │   ├── saas.py             # SaaS Profile
│   │   ├── community.py        # Community Profile
│   │   └── fintech.py          # Fintech Profile
│   └── data_generator_advanced.py
│
├── problems/                   # Problem Management
│   ├── generator.py            # PA Problem Generator
│   ├── generator_stream.py     # Stream Problem Generator
│   ├── prompt_pa.py            # PA Prompts (Type-specific)
│   └── gemini.py               # Gemini API Client
│
├── grader/                     # Grading Logic
│   └── sql_grader.py           # SQL Result Comparison
│
├── engine/                     # Database Engines
│   ├── postgres_engine.py      # PostgreSQL Wrapper
│   └── duckdb_engine.py        # DuckDB Wrapper
│
├── scheduler/                  # Scheduler
│   └── main.py                 # Automated Execution
│
├── docs/                       # Documentation
│   ├── EVENT_TRACKING_GUIDE.md
│   └── EVENT_DESIGN_GUIDELINE.md
│
├── docker-compose.yml          # Container Config
├── .env                        # Environment Variables
└── README.md                   # This Document
```

### 7.2 Environment Variables

```bash
# PostgreSQL
PG_HOST=db
PG_PORT=5432
PG_USER=palab
PG_PASSWORD=your_password
PG_DB=palab

# DuckDB
DUCKDB_PATH=data/pa_lab.duckdb

# Gemini AI
USE_GEMINI=1
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-pro

# Analytics (Frontend)
VITE_MIXPANEL_TOKEN=your_mixpanel_token
VITE_POSTHOG_KEY=your_posthog_key
VITE_POSTHOG_HOST=https://us.i.posthog.com

# Generator
PRODUCT_TYPES=commerce,content,saas,community,fintech
PA_NUM_USERS=50000
```

### 7.3 Local Development

```bash
# Full Stack (Docker)
docker compose up -d

# Frontend Only (Dev Mode)
cd frontend && npm install && npm run dev

# Backend Only (Dev Mode)
cd backend && uvicorn main:app --reload --port 8000

# Scheduler Only
python scheduler/main.py
```

### 7.4 System Architecture

#### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/problems/pa` | GET | PA 문제 목록 |
| `/problems/stream` | GET | Stream 문제 목록 |
| `/problems/schema/{type}` | GET | 스키마 정보 |
| `/execute` | POST | SQL 실행 |
| `/submit` | POST | 정답 제출 |
| `/feedback` | POST | AI 피드백 요청 |
| `/admin/status` | GET | 시스템 상태 |
| `/admin/generate-problems` | POST | 문제 생성 |
| `/admin/refresh-data` | POST | 데이터 갱신 |

#### Request Flow

```
[User SQL Input]
        │
        ▼
[/execute API]
        │
        ▼
[PostgresEngine | DuckDBEngine]
        │
        ▼
[Result Return]
        │
        ├──────────────────────▶ [/submit API]
        │                              │
        │                              ▼
        │                       [SQLGrader]
        │                              │
        │                              ▼
        │                    [Expected Table Comparison]
        │                              │
        │                              ▼
        │                   [Correct / Incorrect]
        │
        └──────────────────────▶ [/feedback API]
                                       │
                                       ▼
                               [Gemini API Call]
                                       │
                                       ▼
                               [AI Feedback Return]
```

### 7.5 Extension Guide

#### Adding New Product Type

```python
# 1. Create Profile (generator/product_profiles/gaming.py)
from .base import BaseProductProfile, Event

class GamingProfile(BaseProductProfile):
    product_type = "gaming"
    
    def generate_session_events(self, user_id, session_id, base_time):
        events = []
        # Event generation logic
        return events

# 2. Register (generator/product_profiles/__init__.py)
from .gaming import GamingProfile
PROFILE_MAP["gaming"] = GamingProfile

# 3. Configure (generator/product_config.py)
PRODUCT_EVENTS["gaming"] = ["login", "play_start", "level_up", ...]
PRODUCT_PROBABILITIES["gaming"] = {"level_up": 0.3, ...}

# 4. Add Prompt Context (problems/prompt_pa.py)
PRODUCT_TYPE_CONTEXTS["gaming"] = {
    "name": "Gaming Platform",
    "requesters": [...],
    "topics": [...]
}
```

---

## 8. Analysis Guide

### 8.1 Getting Started

1. **PA 또는 Stream 탭 선택**
2. **문제 선택** (난이도별 정렬)
3. **스키마 확인** (테이블/컬럼 정보)
4. **SQL 작성** (Monaco 에디터)
5. **실행** (결과 미리보기)
6. **제출** (채점)
7. **피드백 요청** (AI 리뷰)

### 8.2 Problem Example

```
[PM팀 요청]
이번 주 신규 가입자의 Day 1 Retention을 알고 싶습니다.
결과에는 가입일(signup_date), 가입자 수(signups), 
D1 재방문자 수(d1_retained), D1 리텐션율(d1_retention) 컬럼이 필요합니다.
가입일 기준 내림차순 정렬해주세요.
```

### 8.3 Problem Categories

| Category | Difficulty | Description | SQL Techniques |
|----------|------------|-------------|----------------|
| Funnel Analysis | Easy~Medium | 전환율, 이탈 구간 | COUNT, GROUP BY |
| Retention Analysis | Medium | Day N Retention | DATE_TRUNC, LAG |
| Cohort Analysis | Medium~Hard | 가입 시점별 패턴 | Window Functions |
| Segment Analysis | Medium | 그룹별 비교 | CASE WHEN, JOIN |
| Revenue Analysis | Easy~Hard | ARPU, LTV | SUM, AVG |
| Marketing Analysis | Medium | 채널별 성과 | UNION, CTE |

### 8.4 Data Schema

#### PA Tables

```sql
pa_users (
    user_id TEXT PRIMARY KEY,
    signup_at TIMESTAMP,
    country TEXT,
    channel TEXT
)

pa_sessions (
    session_id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES pa_users,
    started_at TIMESTAMP,
    device TEXT
)

pa_events (
    event_id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES pa_users,
    session_id TEXT REFERENCES pa_sessions,
    event_time TIMESTAMP,
    event_name TEXT
)

pa_orders (
    order_id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES pa_users,
    order_time TIMESTAMP,
    amount INT
)
```

#### Stream Tables

```sql
stream_events (
    user_id INT,
    session_id TEXT,
    event_name TEXT,
    event_time TIMESTAMP,
    device TEXT,
    channel TEXT
)

stream_daily_metrics (
    date DATE,
    revenue FLOAT,
    purchases INT
)
```

### 8.5 Event Catalog (Commerce)

| Event | Description |
|-------|-------------|
| `page_view` | 페이지 조회 |
| `view_product` | 상품 조회 |
| `view_review` | 리뷰 조회 |
| `add_to_cart` | 장바구니 추가 |
| `remove_from_cart` | 장바구니 제거 |
| `begin_checkout` | 결제 시작 |
| `apply_coupon` | 쿠폰 적용 |
| `purchase` | 구매 완료 |
| `reorder` | 재구매 |
| `refund_request` | 환불 요청 |
| `search` | 검색 |
| `wishlist_add` | 위시리스트 추가 |
| `compare_product` | 상품 비교 |
| `bundle_view` | 번들 상품 조회 |
| `notification_open` | 알림 열기 |

---

## 9. Documentation

| Document | Path | Description |
|----------|------|-------------|
| Event Tracking Guide | [docs/EVENT_TRACKING_GUIDE.md](./docs/EVENT_TRACKING_GUIDE.md) | Implementation Guide |
| Event Design Guideline | [docs/EVENT_DESIGN_GUIDELINE.md](./docs/EVENT_DESIGN_GUIDELINE.md) | Design Specification |
| API Documentation | http://localhost:8000/docs | Swagger UI |

---

## 10. Roadmap

### v1.0 (Current)
- [x] PA/Stream Problem Solving
- [x] Auto Grading
- [x] AI Feedback (Gemini)
- [x] 5 Product Types
- [x] Event Tracking

### v1.1 (Planned)
- [ ] User Authentication (Google/Kakao)
- [ ] Problem Bookmarks
- [ ] Submission History Persistence
- [ ] Leaderboard

### v2.0 (Future)
- [ ] Custom Problem Creation
- [ ] Team/Group Features
- [ ] Learning Curriculum
- [ ] Certificate Issuance

---

## License

Internal Use Only

---

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

**Built with ❤️ for aspiring product analysts**
