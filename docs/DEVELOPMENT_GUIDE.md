# QueryCraft Development Guide

이 문서는 QueryCraft 프로젝트를 로컬 환경에서 실행하고 개발하기 위한 가이드입니다.

## 🚀 시작하기

### 📝 환경 설정

`.env` 파일을 생성하고 Google Gemini API 키를 설정하세요.

```bash
cp .env.example .env
# GEMINI_API_KEY=your_key_here
```

### 🐳 서비스 실행 (Docker)
Docker Compose로 프론트엔드, 백엔드, DB를 한 번에 실행합니다.
```bash
docker compose up -d
```
- **Web**: `http://localhost:15173`
- **API Docs**: `http://localhost:15174/docs`

### 🏗️ 초기 셋업

실습을 위한 기초 데이터와 오늘자 문제를 생성합니다.

```bash
docker compose exec backend python -c "from backend.api.admin import initial_setup; initial_setup()"
```

## 🛠️ 개발 워크플로우

### 백엔드 (FastAPI)

- `backend/` 디렉토리에서 작업을 수행합니다.
- 변경 사항은 Docker 컨테이너 재시작 시 반영됩니다.

### 프론트엔드 (React + Vite)

- `frontend/` 디렉토리에서 작업을 수행합니다.
- 디자인 시스템 토큰은 `frontend/src/styles/tokens.css`에서 관리합니다.

## 🧪 테스트 실행

```bash
# 전체 테스트 실행
docker compose exec backend pytest
```
