# OAuth 연동 가이드 (SSO)

이 문서는 SQL Labs 프로젝트에 Google 및 Kakao 소셜 로그인을 연동하기 위한 설정 방법을 안내합니다.

## 1. Google OAuth 설정

1. **Google Cloud Console** 접속: [https://console.cloud.google.com/](https://console.cloud.google.com/)
2. **프로젝트 선택** 또는 새 프로젝트 생성
3. **API 및 서비스 > OAuth 동의 화면** 설정
   - User Type: `외부` 선택
   - 앱 이름, 사용자 지원 이메일 등 필수 정보 입력
   - 범위(Scope): `.../auth/userinfo.email`, `.../auth/userinfo.profile` 추가
4. **API 및 서비스 > 사용자 인증 정보**
   - `사용자 인증 정보 만들기` > `OAuth 클라이언트 ID` 클릭
   - 애플리케이션 유형: `웹 애플리케이션`
   - **승인된 리디렉션 URI**:
     - 로컬 개발용: `http://localhost:15174/auth/google/callback`
     - 배포용: `https://your-domain.com/api/auth/google/callback`
5. 발급된 **클라이언트 ID**와 **클라이언트 보안 비밀번호**를 복사합니다.

## 2. Kakao OAuth 설정

1. **Kakao Developers** 접속: [https://developers.kakao.com/](https://developers.kakao.com/)
2. **내 애플리케이션 > 애플리케이션 추가하기**
3. **제품 설정 > 카카오 로그인**:
   - 카카오 로그인 활성화: `ON`
   - **Redirect URI**:
     - 로컬 개발용: `http://localhost:15174/auth/kakao/callback`
     - 배포용: `https://your-domain.com/api/auth/kakao/callback`
4. **제품 설정 > 카카오 로그인 > 동의항목**:
   - 닉네임: `필수 동의`
   - 카카오계정(이메일): `선택 동의` (필요 시 필수)
5. **앱 설정 > 앱 키**:
   - **REST API 키**를 복사합니다 (이것이 `KAKAO_CLIENT_ID`가 됩니다).
6. **제품 설정 > 카카오 로그인 > 보안**:
   - Client Secret 코드를 생성하고 확인합니다 (필요 시).

## 3. 환경변수 설정 (.env)

프로젝트 루트 디렉토리의 `.env` 파일에 발급받은 키를 입력합니다.

```bash
# Google OAuth
GOOGLE_CLIENT_ID=여러분의_구글_클라이언트_ID
GOOGLE_CLIENT_SECRET=여러분의_구글_보안_비밀번호

# Kakao OAuth
KAKAO_CLIENT_ID=여러분의_카카오_REST_API_키
KAKAO_CLIENT_SECRET=여러분의_카카오_클라이언트_시크릿 (설정한 경우)

# Frontend URL (Redirect 처리에 사용됨)
FRONTEND_URL=http://localhost:15173
```

## 4. 적용 방법

환경변수를 수정한 후에는 컨테이너를 재시작해야 적용됩니다.

```bash
docker compose restart backend
```
