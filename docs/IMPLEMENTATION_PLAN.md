# README.md Markdown Lint(MD031) 수정 계획

`README.md`에서 발견된 MD031(blanks-around-fences) 오류를 해결하기 위해 코드 블록 앞뒤에 빈 줄을 추가합니다.

## Proposed Changes

### [Documentation]

#### [MODIFY] [README.md](file:///mnt/z/GitHub/QueryCraft/README.md)

1.  **Mermaid 아키텍처 다이어그램 블록 (L51-L80)**
    - L50과 L51 사이에 빈 줄 추가
    - L80 혹은 L81 이전에 빈 줄 추가
2.  **Bash 도커 실행 예시 블록 (L136-L138)**
    - L138과 L139 사이에 빈 줄 추가

## Verification Plan

### Automated Tests
- 마크다운 렌더링 확인 (수동 확인 필요)

### Manual Verification
- `README.md` 파일을 열어 코드 블록 전후에 공백이 적절히 배치되었는지 확인합니다.
