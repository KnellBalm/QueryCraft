---
name: generate-problem
description: Generate SQL practice problems using Gemini AI. Use when creating new problems, testing problem generation, or when user mentions "문제 생성", "generate problem".
---

# Generate Problem

Gemini 2.0 Flash를 사용해 SQL 연습 문제를 생성합니다.

## Instructions

1. **환경 확인**:
   - `GEMINI_API_KEY` 환경변수 설정 필요
   - `.env` 또는 `.env.dev` 파일에서 로드

2. **문제 유형 선택**:
   - **PA (Product Analytics)**: 비즈니스 분석 문제
   - **Stream**: 실시간 데이터 분석 문제

3. **산업군 선택** (5개 프로필):
   - `commerce` - TrendPick (이커머스)
   - `saas` - TaskSync (B2B SaaS)
   - `content` - InsightFlow (콘텐츠)
   - `community` - HobbyLink (커뮤니티)
   - `fintech` - SafePay (핀테크)

4. **생성 실행**:
   ```bash
   export PYTHONPATH=$PYTHONPATH:$(pwd)
   python -c "from backend.generator.generator import generate_daily_problem; generate_daily_problem('commerce')"
   ```

5. **결과 확인**:
   - 생성된 문제는 `backend/generator/daily/` 디렉토리에 저장
   - 날짜별 파일명 형식: `pa_YYYYMMDD.json`

## Key Files

- `backend/generator/generator.py` - PA 문제 생성
- `backend/generator/generator_stream.py` - Stream 문제 생성
- `backend/generator/product_profiles/` - 산업별 설정
- `backend/generator/prompt_pa.py` - PA 프롬프트 템플릿
