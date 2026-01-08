# Production Deployment Plan

## 현재 상황

상용 환경에서 발생한 오류들:

1. ❌ **DB 스키마 누락 (problems)**: `problems` 테이블에 `updated_at` 컬럼 없음
2. ❌ **DB 스키마 불일치 (api_usage_logs)**: `purpose` 컬럼 없어서 API 사용량 로깅 실패
3. ❌ **SQL 주석 오류**: Gemini 생성 SQL에 주석 포함 시 실행 실패
4. ⚠️ **Windows 폰트**: 윈도우에서 폰트 렌더링 품질 저하

## 배포 순서 (중요!)

### Step 1: DB 마이그레이션 실행

**Supabase SQL Editor**에서 아래 SQL 실행:

```sql
-- 1) problems 테이블 수정
ALTER TABLE public.problems 
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();

-- 2) api_usage_logs 테이블 수정
ALTER TABLE public.api_usage_logs 
ADD COLUMN IF NOT EXISTS purpose VARCHAR(100);

ALTER TABLE public.api_usage_logs 
ADD COLUMN IF NOT EXISTS timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE public.api_usage_logs 
ADD COLUMN IF NOT EXISTS total_tokens INTEGER DEFAULT 0;
```

### Step 2: 코드 배포

```bash
git push origin main
# GCP Cloud Build가 자동으로 배포 진행
```

### Step 3: 검증

1. 관리자 페이지 접속
2. "문제 생성" 버튼 클릭
3. 로그 확인:
   - ✅ `saved 12 problems to DB`
   - ✅ `API usage logged`
4. Windows 브라우저에서 폰트 품질 확인

## 수정 내역

### 백엔드

- SQL 주석 제거: `problems/generator.py`, `problems/generator_stream.py`
- DB 스키마 업데이트: `backend/services/db_init.py`
- 마이그레이션 스크립트: `backend/migrations/`

### 프론트엔드

- Windows 폰트 개선: `frontend/src/index.css` (Malgun Gothic, Noto Sans KR 추가)

---

**날짜**: 2026-01-08  
**커밋**: main 브랜치 최신


