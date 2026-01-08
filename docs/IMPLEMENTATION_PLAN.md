# Production DB Fix - Implementation Plan

## 문제 요약

상용 환경에서 문제 생성 시 2가지 오류 발생:

1. **`updated_at` 컬럼 누락**: `problems` 테이블에 `updated_at` 컬럼이 없어서 모든 문제 저장 실패
2. **SQL 주석 처리 오류**: Gemini가 생성한 정답 SQL에 주석(`--`, `/* */`)이 포함된 경우 실행 오류

## 해결 방법

### 1. DB 스키마 마이그레이션

**마이그레이션 스크립트**: `backend/migrations/add_problems_updated_at.py`

**실행 방법** (상용 환경):
```bash
# Cloud Run 컨테이너 내부에서 실행
python3 /app/backend/migrations/add_problems_updated_at.py
```

**대안** (Supabase SQL Editor):
```sql
ALTER TABLE public.problems 
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();
```

### 2. SQL 주석 제거 로직 추가

**수정된 파일**:
- `problems/generator.py` - PA 문제 생성기
- `problems/generator_stream.py` - Stream 문제 생성기

**변경 내용**: 정규표현식으로 SQL 주석 제거 (`--`, `/* */`)

## 배포 절차

### Step 1: 상용 DB 마이그레이션 실행

> [!WARNING]
> 코드 배포 전에 반드시 DB 마이그레이션을 먼저 실행해야 합니다.

**Supabase SQL Editor에서 실행 (권장)**:
```sql
-- updated_at 컬럼 추가
ALTER TABLE public.problems 
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();

-- 확인
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'problems' AND column_name = 'updated_at';
```

### Step 2: 코드 병합 및 배포

```bash
# main 브랜치로 병합
git checkout main
git merge dev
git push origin main

# GCP Cloud Build가 자동으로 배포 진행
```

### Step 3: 검증

1. 관리자 페이지 접속
2. "문제 생성" 버튼 클릭
3. 로그 확인: `saved 12 problems to DB` 성공 메시지 확인

## 영향도

- **Breaking Change**: 없음
- **Downtime**: 없음
- **Rollback**: `ALTER TABLE problems DROP COLUMN updated_at;`

---

**작성일**: 2026-01-08  
**작성자**: AI Assistant  
**관련 이슈**: Production problem generation failures
