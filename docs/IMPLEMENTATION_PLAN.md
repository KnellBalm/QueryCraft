# 카카오/구글 SSO 로그인 구현 계획

## 📋 현재 상태 분석

### ✅ 이미 구현된 부분

**백엔드 (`backend/api/auth.py`):**
- Google OAuth 완전 구현 (L228-298)
  - `GET /api/auth/google/login` - 로그인 시작
  - `GET /api/auth/google/callback` - OAuth 콜백 처리
- Kakao OAuth 완전 구현 (L304-379)
  - `GET /api/auth/kakao/login` - 로그인 시작
  - `GET /api/auth/kakao/callback` - OAuth 콜백 처리
- 세션 관리, 사용자 저장 로직 구현됨

**프론트엔드 (`frontend/src/components/LoginModal.tsx`):**
- Google/Kakao 로그인 버튼 UI 존재
- `handleSocialLogin` 함수가 `alert()`만 표시 (미연결)

### ❌ 필요한 작업

| 영역 | 필요 작업 |
|------|----------|
| **프론트엔드** | `handleSocialLogin`에서 실제 OAuth URL로 리다이렉트 |
| **환경변수** | Google/Kakao OAuth 키 설정 확인 ([상세 가이드](file:///mnt/z/GitHub/Offline-Lab/docs/OAUTH_SETUP_GUIDE.md)) |

---

## 📂 Proposed Changes

### Frontend

#### [MODIFY] [LoginModal.tsx](file:///mnt/z/GitHub/Offline-Lab/frontend/src/components/LoginModal.tsx)

`handleSocialLogin` 함수 수정:

```diff
  const handleSocialLogin = (provider: string) => {
-     alert(`${provider} 로그인은 아직 준비 중입니다.`);
+     // 백엔드 OAuth 엔드포인트로 리다이렉트
+     const authUrl = provider === 'Google' 
+       ? '/api/auth/google/login'
+       : '/api/auth/kakao/login';
+     window.location.href = authUrl;
  };
```

---

## 🔧 환경변수 (이미 백엔드에서 사용 중)

```bash
# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Kakao OAuth
KAKAO_CLIENT_ID=your-kakao-client-id
KAKAO_CLIENT_SECRET=your-kakao-client-secret

# Frontend URL (콜백 리다이렉트용)
FRONTEND_URL=http://localhost:15173
```

---

## ✅ Verification Plan

### Manual Verification

1. **프론트엔드 빌드 확인**
   ```bash
   cd /mnt/z/GitHub/Offline-Lab/frontend && npm run build
   ```

2. **SSO 로그인 플로우 테스트**
   - 로그인 모달에서 "Google로 계속하기" 클릭
   - Google OAuth 화면으로 리다이렉트 확인
   - 로그인 후 메인 페이지로 돌아와 로그인 상태 확인

3. **카카오 로그인 테스트** (위와 동일한 방식)

### 환경변수 미설정 시

- OAuth 클라이언트 키가 없으면 백엔드가 `400 OAuth not configured` 반환
- `/api/auth/status` 엔드포인트로 설정 상태 확인 가능

---

## ⚠️ User Review Required

> [!IMPORTANT]
> **OAuth 앱 설정 필요**
> - Google Cloud Console에서 OAuth 앱 생성 및 Redirect URI 등록 필요
> - Kakao Developers에서 앱 생성 및 Redirect URI 등록 필요
> - Redirect URI: `http://localhost:15174/auth/google/callback`, `http://localhost:15174/auth/kakao/callback`
