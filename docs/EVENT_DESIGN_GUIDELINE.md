# 이벤트 설계 가이드라인 (AI 에이전트용)

> 서비스 기획의도를 파악하여 최대한 세부적이고 포괄적인 이벤트를 설계하기 위한 가이드라인

---

## 1. 서비스 분석 단계

### 1.1 기획 의도 파악 질문

에이전트가 반드시 답해야 할 질문:
```
1. 이 서비스의 핵심 가치는?
   - 사용자가 이 서비스를 왜 사용하는가?
   - 어떤 문제를 해결하는가?

2. 비즈니스 모델은?
   - 어떻게 수익을 창출하는가?
   - 무료→유료 전환 포인트는?

3. 타겟 사용자는?
   - 주 사용자 페르소나는?
   - 파워 유저와 일반 유저의 차이는?

4. 핵심 성공 지표(North Star Metric)는?
   - DAU/MAU? 전환율? 리텐션? ARPU?

5. 핵심 사용자 여정은?
   - 첫 방문 → [???] → 가치 경험 → 재방문
```

### 1.2 서비스 유형별 분석 프레임워크

| 서비스 유형 | 핵심 여정 | 핵심 지표 | 주요 이벤트 영역 |
|------------|----------|----------|-----------------|
| **이커머스** | 검색→상품조회→장바구니→결제 | GMV, 전환율, AOV | 상품, 장바구니, 결제, 검색 |
| **콘텐츠** | 방문→콘텐츠소비→공유→구독 | DAU, 완독률, 구독전환 | 조회, 스크롤, 공유, 구독 |
| **SaaS** | 가입→온보딩→기능사용→업그레이드 | Activation, Retention, MRR | 기능사용, 온보딩, 플랜변경 |
| **소셜** | 가입→콘텐츠생성→상호작용→재방문 | DAU, 콘텐츠생성률, 참여율 | 포스팅, 좋아요, 댓글, 팔로우 |
| **핀테크** | 가입→KYC→첫거래→반복거래 | 거래량, 거래액, 리텐션 | 거래, 송금, 결제, 인증 |
| **게임** | 설치→튜토리얼→레벨업→결제 | DAU, 리텐션, ARPU | 레벨업, 아이템, 결제, 이탈 |
| **학습** | 가입→첫학습→완료→재학습 | 완료율, 리텐션, 학습시간 | 시작, 진행, 완료, 성적 |

---

## 2. 이벤트 분류 체계 (Event Taxonomy)

### 2.1 5대 이벤트 카테고리

모든 서비스에서 수집해야 할 이벤트 카테고리:

```
1. LIFECYCLE - 사용자 생애주기
2. NAVIGATION - 탐색/이동
3. ENGAGEMENT - 참여/인터랙션
4. CONVERSION - 전환
5. SYSTEM - 시스템/에러
```

### 2.2 카테고리별 세부 이벤트

#### LIFECYCLE (생애주기)
```
user_signup              # 회원가입
user_login               # 로그인
user_logout              # 로그아웃
user_profile_update      # 프로필 수정
user_password_change     # 비밀번호 변경
user_subscription_start  # 구독 시작
user_subscription_cancel # 구독 취소
user_account_delete      # 계정 삭제
user_reactivate          # 재활성화 (휴면 복귀)
```

#### NAVIGATION (탐색)
```
page_view                # 페이지 조회
page_leave               # 페이지 이탈
tab_change               # 탭 변경
menu_click               # 메뉴 클릭
search_start             # 검색 시작
search_submit            # 검색 실행
search_result_click      # 검색 결과 클릭
filter_apply             # 필터 적용
sort_change              # 정렬 변경
pagination               # 페이지네이션
breadcrumb_click         # 경로 탐색 클릭
back_button              # 뒤로가기
```

#### ENGAGEMENT (참여)
```
button_click             # 버튼 클릭
form_start               # 폼 입력 시작
form_field_focus         # 폼 필드 포커스
form_field_blur          # 폼 필드 벗어남
form_submit              # 폼 제출
modal_open               # 모달 열림
modal_close              # 모달 닫힘
tooltip_view             # 툴팁 조회
dropdown_open            # 드롭다운 열림
toggle_switch            # 토글 스위치
scroll_depth_25          # 스크롤 25%
scroll_depth_50          # 스크롤 50%
scroll_depth_75          # 스크롤 75%
scroll_depth_100         # 스크롤 100%
time_on_page_30s         # 30초 체류
time_on_page_60s         # 60초 체류
time_on_page_180s        # 3분 체류
copy_text                # 텍스트 복사
share_click              # 공유 클릭
download_click           # 다운로드 클릭
print_click              # 인쇄 클릭
```

#### CONVERSION (전환)
```
cta_click                # CTA 버튼 클릭
trial_start              # 무료체험 시작
trial_end                # 무료체험 종료
upgrade_click            # 업그레이드 클릭
upgrade_complete         # 업그레이드 완료
payment_start            # 결제 시작
payment_complete         # 결제 완료
payment_fail             # 결제 실패
checkout_start           # 체크아웃 시작
checkout_abandon         # 체크아웃 이탈
add_to_cart              # 장바구니 추가
remove_from_cart         # 장바구니 제거
purchase                 # 구매 완료
refund_request           # 환불 요청
```

#### SYSTEM (시스템)
```
error_api                # API 에러
error_client             # 클라이언트 에러
error_validation         # 유효성 검사 에러
loading_slow             # 느린 로딩 (>3초)
session_timeout          # 세션 타임아웃
network_offline          # 네트워크 오프라인
network_online           # 네트워크 복구
app_crash                # 앱 크래시
feature_flag_exposed     # 피처플래그 노출
experiment_assigned      # 실험군 배정
```

---

## 3. 서비스별 맞춤 이벤트 설계

### 3.1 이커머스

```
# 상품
product_view             # 상품 조회
product_image_zoom       # 상품 이미지 확대
product_review_view      # 리뷰 조회
product_review_write     # 리뷰 작성
product_compare          # 상품 비교
product_wishlist_add     # 위시리스트 추가
product_wishlist_remove  # 위시리스트 제거
product_share            # 상품 공유
product_out_of_stock     # 품절 조회

# 장바구니
cart_view                # 장바구니 조회
cart_add                 # 장바구니 추가
cart_remove              # 장바구니 제거
cart_quantity_change     # 수량 변경
cart_coupon_apply        # 쿠폰 적용
cart_coupon_fail         # 쿠폰 적용 실패

# 결제
checkout_shipping_select # 배송지 선택
checkout_payment_select  # 결제수단 선택
checkout_confirm_view    # 주문 확인 조회
order_complete           # 주문 완료
order_cancel             # 주문 취소
order_track              # 배송 추적
```

### 3.2 콘텐츠 플랫폼

```
# 콘텐츠 소비
content_view             # 콘텐츠 조회
content_start            # 콘텐츠 시작 (영상/오디오)
content_pause            # 일시정지
content_resume           # 재개
content_complete         # 완료
content_skip             # 건너뛰기
content_progress_25      # 25% 진행
content_progress_50      # 50% 진행
content_progress_75      # 75% 진행
content_speed_change     # 재생속도 변경
content_quality_change   # 화질 변경
content_fullscreen       # 전체화면
content_pip              # PIP 모드

# 인터랙션
content_like             # 좋아요
content_unlike           # 좋아요 취소
content_save             # 저장
content_share            # 공유
content_comment_view     # 댓글 조회
content_comment_write    # 댓글 작성
content_comment_reply    # 답글 작성
content_report           # 신고
```

### 3.3 SaaS

```
# 온보딩
onboarding_start         # 온보딩 시작
onboarding_step_complete # 단계 완료
onboarding_skip          # 건너뛰기
onboarding_complete      # 온보딩 완료

# 기능 사용
feature_use              # 기능 사용
feature_first_use        # 첫 사용
feature_discover         # 기능 발견
feature_error            # 기능 에러

# 협업
invite_send              # 초대 전송
invite_accept            # 초대 수락
invite_reject            # 초대 거절
team_create              # 팀 생성
team_leave               # 팀 탈퇴
permission_change        # 권한 변경

# 통합
integration_connect      # 연동 연결
integration_disconnect   # 연동 해제
api_key_create           # API 키 생성
webhook_configure        # 웹훅 설정
```

### 3.4 소셜/커뮤니티

```
# 콘텐츠 생성
post_start               # 포스팅 시작
post_draft_save          # 임시저장
post_publish             # 게시
post_edit                # 수정
post_delete              # 삭제
post_repost              # 리포스트
post_quote               # 인용

# 소셜 인터랙션
follow                   # 팔로우
unfollow                 # 언팔로우
block                    # 차단
unblock                  # 차단 해제
mute                     # 뮤트
dm_send                  # DM 전송
dm_read                  # DM 읽음
mention                  # 멘션
hashtag_click            # 해시태그 클릭

# 프로필
profile_view             # 프로필 조회
profile_photo_change     # 프로필 사진 변경
profile_bio_update       # 소개 수정
profile_link_click       # 프로필 링크 클릭
```

### 3.5 학습/교육

```
# 학습 진행
lesson_start             # 강의 시작
lesson_progress          # 진행률 이벤트
lesson_complete          # 강의 완료
lesson_bookmark          # 북마크
lesson_note_create       # 노트 작성
lesson_question          # 질문 작성

# 평가/퀴즈
quiz_start               # 퀴즈 시작
quiz_answer              # 답변 제출
quiz_correct             # 정답
quiz_incorrect           # 오답
quiz_hint_request        # 힌트 요청
quiz_complete            # 퀴즈 완료

# 학습 관리
course_enroll            # 수강 신청
course_complete          # 수료
certificate_download     # 수료증 다운로드
study_time_log           # 학습시간 기록
```

---

## 4. 이벤트 속성 (Properties) 설계

### 4.1 공통 속성 (모든 이벤트에 자동 포함)

```typescript
{
  // 시간
  timestamp: string,           // ISO 8601
  local_time: string,          // 사용자 로컬 시간
  
  // 세션
  session_id: string,
  session_number: number,      // 해당 사용자의 몇 번째 세션인지
  
  // 사용자
  user_id?: string,
  is_logged_in: boolean,
  
  // 위치
  page_url: string,
  page_path: string,
  page_title: string,
  referrer: string,
  
  // 환경
  device_type: 'desktop' | 'mobile' | 'tablet',
  browser: string,
  os: string,
  screen_resolution: string,
  language: string,
  timezone: string,
  
  // UTM
  utm_source?: string,
  utm_medium?: string,
  utm_campaign?: string,
  utm_content?: string,
  utm_term?: string,
}
```

### 4.2 이벤트별 추가 속성

```typescript
// 버튼 클릭
button_click: {
  button_id: string,
  button_text: string,
  button_type: 'primary' | 'secondary' | 'cta',
  section: string,          // 버튼이 있는 섹션
}

// 페이지 조회
page_view: {
  page_type: string,        // 'home' | 'product' | 'checkout' 등
  load_time_ms: number,     // 페이지 로드 시간
  is_first_view: boolean,   // 첫 방문인지
}

// 상품 조회
product_view: {
  product_id: string,
  product_name: string,
  product_category: string,
  product_price: number,
  product_currency: string,
  product_brand?: string,
  product_position?: number, // 리스트에서의 위치
}

// 스크롤
scroll_depth: {
  depth_percent: number,
  depth_pixels: number,
  content_length: number,
  time_to_reach_ms: number,
}

// 에러
error: {
  error_type: string,
  error_message: string,
  error_code?: string,
  error_stack?: string,
  api_endpoint?: string,
}

// 검색
search: {
  search_term: string,
  search_type: 'text' | 'voice' | 'visual',
  results_count: number,
  has_results: boolean,
}
```

---

## 5. 이벤트 설계 체크리스트

### 5.1 완전성 체크 (Completeness)

```
[ ] 사용자 여정의 모든 단계에 이벤트가 있는가?
    - 첫 방문
    - 가입/로그인
    - 핵심 기능 사용
    - 가치 경험 (Aha Moment)
    - 전환
    - 재방문

[ ] 모든 UI 요소에 이벤트가 있는가?
    - 버튼
    - 링크
    - 폼
    - 탭/메뉴
    - 모달

[ ] 모든 에러 상황에 이벤트가 있는가?
    - API 에러
    - 유효성 검사 실패
    - 네트워크 문제
    - 권한 부족

[ ] 성능 관련 이벤트가 있는가?
    - 페이지 로드 시간
    - 느린 API 응답
    - 긴 렌더링 시간
```

### 5.2 세분화 체크 (Granularity)

```
[ ] 단순 행동이 아닌 세부 맥락을 수집하는가?
    - ❌ button_click
    - ✅ button_click + { button_id, section, cta_type }

[ ] 결과를 알 수 있는가?
    - ❌ form_submit
    - ✅ form_submit + { success, error_message, fields_filled }

[ ] 소요 시간을 수집하는가?
    - ❌ lesson_complete
    - ✅ lesson_complete + { duration_seconds, pauses_count }

[ ] 시퀀스를 파악할 수 있는가?
    - ❌ page_view (단독)
    - ✅ page_view + { previous_page, navigation_type }
```

### 5.3 분석 가능성 체크 (Analyzability)

```
[ ] 퍼널 분석이 가능한가?
    - 각 단계별 이벤트 정의됨
    - 이탈 지점 파악 가능

[ ] 코호트 분석이 가능한가?
    - 가입일 기준 그룹핑 가능
    - 세그먼트별 속성 있음

[ ] 리텐션 분석이 가능한가?
    - 반복 행동 추적 가능
    - 재방문 식별 가능

[ ] A/B 테스트가 가능한가?
    - 실험군/대조군 속성 있음
    - variant 정보 포함

[ ] 경로 분석이 가능한가?
    - 페이지 이동 추적
    - 기능 사용 순서 파악
```

---

## 6. 이벤트 설계 프로세스 (AI 에이전트용)

### Step 1: 서비스 파악
```
1. 서비스 README/문서 읽기
2. 핵심 기능 목록 작성
3. 사용자 페르소나 정의
4. 핵심 사용자 여정 그리기
```

### Step 2: 이벤트 도출
```
1. 각 페이지별 이벤트 나열
2. 각 컴포넌트별 이벤트 나열
3. 에러 상황 이벤트 추가
4. 성능 이벤트 추가
```

### Step 3: 속성 정의
```
1. 공통 속성 정의
2. 이벤트별 필수 속성 정의
3. 분석 질문 기반 속성 추가
```

### Step 4: 검증
```
1. 완전성 체크리스트 확인
2. 세분화 체크리스트 확인
3. 분석 가능성 체크리스트 확인
```

### Step 5: 구현
```
1. analytics.ts 서비스 생성
2. 이벤트 타입 정의
3. 각 컴포넌트에 이벤트 호출 추가
4. 테스트 및 검증
```

---

## 7. 이벤트 설계 프롬프트 템플릿

다른 AI 에이전트에게 이벤트 설계를 시킬 때 사용:

```
# 이벤트 설계 요청

## 서비스 정보
- 서비스명: [서비스 이름]
- 서비스 유형: [이커머스/콘텐츠/SaaS/소셜/핀테크/학습/기타]
- 핵심 기능: [핵심 기능 나열]
- 타겟 사용자: [타겟 사용자 설명]

## 요청 사항
위 서비스에 대해 최대한 세부적이고 포괄적인 이벤트 트래킹을 설계해주세요.

## 출력 형식
1. 핵심 사용자 여정 (5단계 이상)
2. 이벤트 목록 (카테고리별, 최소 50개)
3. 각 이벤트의 속성 정의
4. analytics.ts 구현 코드
5. 컴포넌트별 이벤트 호출 예시

## 체크리스트
- [ ] 모든 페이지에 page_view 이벤트
- [ ] 모든 버튼에 click 이벤트
- [ ] 모든 폼에 submit 이벤트
- [ ] 모든 에러에 error 이벤트
- [ ] 스크롤 깊이 이벤트
- [ ] 체류 시간 이벤트
- [ ] 기능 사용 이벤트
- [ ] 전환 이벤트
```

---

## 8. 예시: 이 프로젝트 (SQL Analytics Lab)

### 서비스 분석
- **유형**: 학습 플랫폼
- **핵심 가치**: SQL 실습을 통한 프로덕트 분석 역량 향향 (KST 기반 실무 시뮬레이션)
- **핵심 여정**: Page Viewed → Problem Viewed → Problem Attempted → Problem Submitted → Problem Solved ⭐

### 이벤트 목록 (핵심 25개)
```text
# NAVIGATION
Page Viewed
Tab Changed
Schema Viewed

# PROBLEM FLOW (Funnel)
Problem Viewed
Problem Attempted
Problem Submitted
Problem Solved ⭐
Problem Failed
Hint Requested

# SQL INTERACTION
SQL Executed
SQL Error Occurred

# USER LIFECYCLE
Sign Up Completed
Login Success
Logout Completed

# SYSTEM & ADMIN
Onboarding Started
Onboarding Completed
Admin Trigger Daily Generation
Admin Refresh Data
```

이 가이드라인을 따르면 어떤 서비스든 포괄적인 이벤트 트래킹을 설계할 수 있습니다.
