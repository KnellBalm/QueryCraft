# TODO List

## 백엔드 API 에러 해결 마무리
- [ ] 백엔드 API 최종 동작 검증
  - [ ] Leaderboard (500) 해결 확인
  - [ ] Recommend (400) 해결 확인
  - [ ] Translate (404) 해결 확인
- [ ] `dev` 브랜치 소스 푸시 (작업 완료 후 TODO List 삭제 예정)

## 스케줄러 개선 (Cloud Run)
- [ ] 전용 스케줄 엔드포인트 설계: `/admin/schedule/run`
- [ ] 전용 엔드포인트 구현: 데이터+문제 생성 실행
- [ ] 관리자 인증: OIDC 토큰 또는 관리자 API 키 검증
- [ ] 성공/실패 로그 및 반환 포맷 정의 (status, counts, duration)
- [ ] 내부 스케줄러 비활성화 또는 중복 실행 방지 플래그 추가

## Cloud Scheduler 설정
- [ ] Cron 설정: `0 1 * * *` (TZ: `Asia/Seoul`)
- [ ] Scheduler → Cloud Run HTTP 트리거 연결
- [ ] 서비스 계정 생성 및 Cloud Run Invoker 권한 부여
- [ ] 재시도 정책 설정 (예: 최대 3회, 지수 백오프)
- [ ] 실패 알림 설정 (로그 기반 알람/슬랙/이메일)

## 배포/운영 점검
- [ ] `ENV=production` 및 `ENABLE_SCHEDULER` 값 정리
- [ ] 스케줄러 중복 실행 여부 모니터링
- [ ] 생성 결과 검증 (problems/daily 파일 + DB 데이터)

## MixPanel 이벤트 추가 및 개선
- [ ] 신규 기능 이벤트 정의 (이벤트명/속성/샘플 페이로드)
- [ ] `frontend/src/services/analytics.ts` 이벤트 추가 및 사용 위치 연결
- [ ] `docs/EVENT_TRACKING_GUIDE.md`에 이벤트/속성 문서화
- [ ] 스테이징/프로덕션 토큰 분리 및 환경변수 점검
- [ ] 이벤트 수집 검증 (Mixpanel Live View 또는 Network 탭)
- [ ] 분석가용 운영 가이드 작성: `docs/MIXPANEL_ANALYST_GUIDE.md`
- [ ] PA 핵심 퍼널/리텐션/코호트 정의 및 대시보드 구성
- [ ] RCA 문제 풀이 흐름 이벤트 정의 및 진입/이탈 분석
- [ ] AI Lab 기능(Translate/Insight) 사용성 지표 정의
- [ ] 실험/버전 지표 정의 (`prompt_version`, `experiment_group`)
- [ ] 데이터 품질 체크리스트(누락/중복/스키마 변경) 마련

