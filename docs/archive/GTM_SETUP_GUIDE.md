# Google Tag Manager (GTM) 및 GA4 설정 가이드

> ⏱️ 예상 소요 시간: 약 20-30분

이 가이드에서는 QueryCraft에 Google Tag Manager를 통한 GA4 분석을 설정하는 방법을 설명합니다.

---

## 📋 목차
1. [GTM 계정 및 컨테이너 생성](#1-gtm-계정-및-컨테이너-생성)
2. [GA4 속성 생성](#2-ga4-속성-생성)
3. [GTM에서 GA4 태그 설정](#3-gtm에서-ga4-태그-설정)
4. [커스텀 이벤트 트래킹 설정](#4-커스텀-이벤트-트래킹-설정)
5. [코드에서 GTM ID 업데이트](#5-코드에서-gtm-id-업데이트)
6. [테스트 및 배포](#6-테스트-및-배포)

---

## 1. GTM 계정 및 컨테이너 생성

### Step 1.1: GTM 접속
1. [tagmanager.google.com](https://tagmanager.google.com) 접속
2. Google 계정으로 로그인

### Step 1.2: 계정 생성
1. **"계정 만들기"** 클릭
2. 정보 입력:
   - 계정 이름: `QueryCraft`
   - 국가: `대한민국`
3. **"계속"** 클릭

### Step 1.3: 컨테이너 생성
| 설정 | 값 |
|------|-----|
| 컨테이너 이름 | `querycraft-web` |
| 타겟 플랫폼 | **웹** |

4. **"만들기"** 클릭
5. 이용약관 동의

### Step 1.4: GTM ID 확인
- 생성 후 표시되는 ID: `GTM-XXXXXXX`
- 📝 이 ID를 메모해두세요

---

## 2. GA4 속성 생성

### Step 2.1: GA4 접속
1. [analytics.google.com](https://analytics.google.com) 접속
2. **"관리"** (⚙️ 아이콘) 클릭

### Step 2.2: 속성 만들기
1. **"속성 만들기"** 클릭
2. 정보 입력:
   - 속성 이름: `QueryCraft`
   - 시간대: `대한민국`
   - 통화: `원 (KRW)`
3. **"다음"** 클릭

### Step 2.3: 비즈니스 정보
- 업종: `교육` 또는 적절한 카테고리
- 비즈니스 규모 선택
- **"만들기"** 클릭

### Step 2.4: 데이터 스트림 생성
1. **"웹"** 선택
2. 정보 입력:
   - 웹사이트 URL: `https://your-domain.com`
   - 스트림 이름: `QueryCraft Web`
3. **"스트림 만들기"** 클릭

### Step 2.5: 측정 ID 확인
- 생성 후 표시되는 ID: `G-XXXXXXXXXX`
- 📝 이 ID를 메모해두세요

---

## 3. GTM에서 GA4 태그 설정

### Step 3.1: GTM으로 돌아가기
1. [tagmanager.google.com](https://tagmanager.google.com) 접속
2. 생성한 컨테이너 선택

### Step 3.2: GA4 구성 태그 생성
1. **"태그"** → **"새로 만들기"** 클릭
2. 태그 이름: `GA4 - Configuration`
3. 태그 유형: **Google 태그** 선택
4. 태그 ID: `G-XXXXXXXXXX` (GA4 측정 ID)
5. 트리거: **All Pages** 선택
6. **"저장"** 클릭

---

## 4. 커스텀 이벤트 트래킹 설정

QueryCraft는 `dataLayer.push()`를 통해 커스텀 이벤트를 전송합니다.

### Step 4.1: 변수 생성

**dataLayer 변수 생성** (각각 만들기):

| 변수 이름 | 데이터 영역 변수 이름 |
|----------|---------------------|
| `DL - problem_id` | `problem_id` |
| `DL - difficulty_level` | `difficulty_level` |
| `DL - attempt_count` | `attempt_count` |
| `DL - data_type` | `data_type` |
| `DL - user_id` | `user_id` |
| `DL - auth_provider` | `auth_provider` |

### Step 4.2: 트리거 생성

**커스텀 이벤트 트리거** (각각 만들기):

| 트리거 이름 | 이벤트 이름 |
|------------|------------|
| `CE - Problem Solved` | `problem_solved` |
| `CE - Problem Viewed` | `problem_viewed` |
| `CE - Login Success` | `login_success` |
| `CE - Sign Up Completed` | `sign_up_completed` |

### Step 4.3: GA4 이벤트 태그 생성

**예시: Problem Solved 태그**

1. **"태그"** → **"새로 만들기"**
2. 태그 이름: `GA4 - Problem Solved`
3. 태그 유형: **Google 애널리틱스: GA4 이벤트**
4. 구성 태그: `GA4 - Configuration` 선택
5. 이벤트 이름: `problem_solved`
6. 이벤트 매개변수:

| 매개변수 이름 | 값 |
|--------------|-----|
| `problem_id` | `{{DL - problem_id}}` |
| `difficulty_level` | `{{DL - difficulty_level}}` |
| `attempt_count` | `{{DL - attempt_count}}` |
| `data_type` | `{{DL - data_type}}` |

7. 트리거: `CE - Problem Solved` 선택
8. **"저장"** 클릭

> 💡 다른 이벤트들도 동일한 방식으로 생성하세요.

---

## 5. 코드에서 GTM ID 업데이트

### Step 5.1: index.html 수정

`frontend/index.html` 파일에서 `GTM-XXXXXXX`를 실제 GTM ID로 교체:

```html
<!-- Google Tag Manager (HEAD) -->
<script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
})(window,document,'script','dataLayer','GTM-XXXXXXX');</script>  <!-- ← 여기 변경 -->
```

```html
<!-- Google Tag Manager (BODY) -->
<noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-XXXXXXX"  <!-- ← 여기도 변경 -->
height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
```

### Step 5.2: 환경변수 사용 (권장)

프로덕션에서는 환경변수를 사용하세요:

1. `.env` 파일에 추가:
```
VITE_GTM_ID=GTM-XXXXXXX
```

2. `index.html`을 동적으로 생성하거나 빌드 시 교체

---

## 6. 테스트 및 배포

### Step 6.1: GTM 미리보기 모드
1. GTM에서 **"미리보기"** 클릭
2. 사이트 URL 입력
3. **"연결"** 클릭

### Step 6.2: 이벤트 테스트
1. 사이트에서 문제 풀기, 로그인 등 동작 수행
2. GTM 미리보기에서 이벤트 발생 확인

### Step 6.3: GA4 DebugView
1. GA4 → **"관리"** → **"DebugView"**
2. 실시간으로 이벤트 확인

### Step 6.4: GTM 게시
1. 테스트 완료 후 GTM에서 **"제출"** 클릭
2. 버전 이름 입력 (예: `v1.0 - Initial GA4 Setup`)
3. **"게시"** 클릭

---

## 📊 주요 이벤트 매핑 (Mixpanel → GA4)

| Mixpanel 이벤트 | GA4 이벤트 (snake_case) |
|----------------|------------------------|
| `Problem Solved` | `problem_solved` |
| `Problem Viewed` | `problem_viewed` |
| `Problem Submitted` | `problem_submitted` |
| `Login Success` | `login_success` |
| `Sign Up Completed` | `sign_up_completed` |
| `SQL Executed` | `sql_executed` |

---

## ⚠️ 주의사항

1. **GTM ID 플레이스홀더**: 현재 코드에 `GTM-XXXXXXX` 플레이스홀더가 있으므로 반드시 실제 ID로 교체하세요.
2. **테스트 필수**: 프로덕션 배포 전 반드시 미리보기 모드에서 테스트하세요.
3. **Consent Mode**: GDPR/개인정보 규정 준수가 필요한 경우 Google Consent Mode를 추가로 설정하세요.
