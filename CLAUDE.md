# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

QueryCraft (쿼리크래프트) is a Korean-first AI-powered SQL learning platform. It teaches business data analysis through realistic scenarios across 5 industry domains (e-commerce, SaaS, content, community, fintech). The platform uses Gemini 2.0 Flash for daily problem generation and personalized feedback.

## Common Commands

### Development Environment
```bash
# Start all services with Docker (recommended)
docker compose -f docker-compose.dev.yml up -d

# Frontend: http://localhost:15173
# Backend API: http://localhost:15174/docs
```

### Backend (Python/FastAPI)
```bash
# Install dependencies
pip install -r requirements.txt

# Run backend locally (requires PYTHONPATH)
export PYTHONPATH=$PYTHONPATH:$(pwd)
uvicorn backend.main:app --reload --port 8080

# Run tests (CI에서 실행하는 테스트)
pytest tests/test_grader.py tests/test_duckdb_engine.py -v

# Run a single test file
pytest tests/test_grader.py -v

# Run a specific test
pytest tests/test_grader.py::test_function_name -v
```

### Frontend (React/TypeScript/Vite)
```bash
cd frontend

# Install dependencies
npm ci

# Development server
npm run dev

# Build (TypeScript check + Vite build)
npm run build

# Lint
npm run lint
```

### Claude Code Skills
```bash
# 백엔드 테스트 + 프론트엔드 빌드/린트 한 번에 실행
/verify

# Gemini AI로 SQL 문제 생성 테스트
/generate-problem
```

## Architecture

### 2-Track Service Model
- **Core Skills (Track A)**: Traditional SQL training - PA problems, Stream problems, Practice mode, Leaderboard
- **Future Lab (Track B)**: AI-powered features - Text-to-SQL, AI Insights, RCA scenarios

### Hybrid Database Strategy
- **PostgreSQL**: Transactional data (users, problems, submissions, leaderboards) via `backend/engine/postgres_engine.py`
- **DuckDB**: Analytical workloads (large event logs, performance metrics) via `backend/engine/duckdb_engine.py`

### Key Directories
- `backend/api/`: REST API routes (problems, sql, stats, auth, admin, practice)
- `backend/services/`: Business logic (grading_service, ai_service, problem_service, recommendation_service)
- `backend/generator/`: AI problem generation with 5 product profiles in `product_profiles/`
- `frontend/src/pages/`: Main views (Workspace, Practice, AILab, MyPage)
- `frontend/src/contexts/`: React Context (AuthContext, ThemeContext, TrackContext)

### Problem Types (Data Types)
- **PA (Product Analytics)**: 일반 비즈니스 분석 문제 (6문제/일)
- **Stream**: 실시간 스트리밍 데이터 분석 문제
- **RCA**: Root Cause Analysis 시나리오 (Future Lab)

### Problem Storage
- 문제 JSON 파일: `problems/daily/` 디렉토리
  - PA: `2026-01-15_commerce.json` (날짜_산업군)
  - Stream: `stream_2026-01-15.json`
  - RCA: `rca_2026-01-15.json`
- 채점용 정답 테이블: PostgreSQL `grading` 스키마에 저장 (e.g., `grading.pa_20260115_01`)

### Problem Generation Flow
1. APScheduler triggers daily at 01:00 KST (or Cloud Scheduler in production)
2. `backend/generator/` creates problems using Gemini 2.0 Flash
3. Problems JSON saved to `problems/daily/`, answer tables to `grading` schema
4. Five product profiles define industry-specific scenarios: commerce, saas, content, community, fintech

### Environment
- All timestamps use KST (Asia/Seoul timezone)
- Environment variables loaded from `.env` or `.env.dev`
- Key env vars: `GEMINI_API_KEY`, `POSTGRES_DSN`, `DUCKDB_PATH`

## CI/CD
- PR to `main`: Runs pytest (backend) and build check (frontend)
- Push to `main`: Deploys to GCP Cloud Run (frontend, backend) and Cloud Functions (workers)

## Key File Locations

| 기능 | 파일 |
|------|------|
| SQL 채점 | `backend/services/grading_service.py` |
| AI 피드백/인사이트 | `backend/services/ai_service.py` |
| 문제 조회/저장 | `backend/services/problem_service.py` |
| 사용자 인증 (OAuth) | `backend/api/auth.py` |
| SQL 실행/검증 | `backend/services/sql_service.py` |
| 문제 생성기 | `backend/generator/data_generator_advanced.py` |
| 스케줄러 | `backend/scheduler.py` |

## Known Issues
- DataFrame 비교 로직 (`grading_service.py:108-142`): 행 단위 반복 사용 중 - 벡터화 필요
- 테스트 커버리지 낮음 (~3.7%) - `tests/` 디렉토리
- 상세 분석: `.claude/PROJECT_ANALYSIS.md` 참고
