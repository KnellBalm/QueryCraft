# 이중 스크롤바 수정 계획

화면 우측에 두 개의 스크롤바가 생기는 문제를 해결하고 레이아웃을 최적화합니다.

## 제안된 변경 사항

### Frontend

#### [MODIFY] [main.tsx](file:///Users/zokr/python_workspace/QueryCraft/frontend/src/main.tsx)
- 누락된 `import './index.css'` 추가하여 전역 스타일 적용 보장

#### [MODIFY] [App.css](file:///Users/zokr/python_workspace/QueryCraft/frontend/src/App.css)
- `.app` 컨테이너에 `box-sizing: border-box` 추가
- 헤더 마진을 앱 전체 패딩으로 이동하여 불필요한 스택 방지
- 독립 스크롤 영역(`.main`)의 스타일 유지 보수

#### [MODIFY] [index.css](file:///Users/zokr/python_workspace/QueryCraft/frontend/src/index.css)
- `html, body, #root`에 `margin: 0 !important`, `padding: 0 !important`, `overflow: hidden !important` 적용하여 브라우저 기본값 및 기타 스타일의 간섭 차단

## 검증 계획

### 수동 검증
1. 브라우저 subagent를 사용하여 `http://localhost:15173` 접속
2. `html.scrollHeight`와 `html.clientHeight`가 동일한지 확인 (정상이라면 윈도우 스크롤바 제거됨)
3. 헤더 영역 마우스 휠 조작 시 윈도우가 흔들리지 않는지 확인
4. 메인 콘텐츠 영역이 독립적으로 스크롤되는지 확인
