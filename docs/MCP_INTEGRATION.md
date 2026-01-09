# QueryCraft MCP (Model Context Protocol) 도입 제안서

본 문서는 QueryCraft 프로젝트의 AI 기능을 강화하기 위해 Model Context Protocol(MCP)을 도입하는 방안을 정리한 문서입니다.

## 1. 개요
MCP는 AI 애플리케이션(LMM)이 외부 데이터 소스나 도구(Tool)에 표준화된 방식으로 접근할 수 있게 해주는 프로토콜입니다. 이를 통해 QueryCraft의 AI는 단순한 코드 생성기를 넘어 실제 데이터베이스 상황을 인지하고 행동하는 '에이전트'로 진화할 수 있습니다.

## 2. 주요 활용 시나리오

### A. 실시간 데이터 기반 AI 튜터 (DB Context Server)
사용자가 SQL 작성 중 어려움을 겪을 때, AI가 현재 DB의 실제 데이터 상태를 파악하여 가이드를 제공합니다.
- **도구(Tools)**:
    - `get_schema(table_name)`: 실제 테이블의 컬럼명, 타입, 제약 조건 조회
    - `preview_data(table_name, limit)`: 테이블의 샘플 데이터를 조회하여 데이터 분포 확인
    - `check_query_plan(sql)`: 사용자 쿼리의 실행 계획(EXPLAIN)을 분석하여 성능 피드백
- **비즈니스 가치**: "쿼리는 맞지만 실제 데이터에 해당 날짜 값이 없습니다"와 같이 데이터에 근거한 정확한 힌트 제공 가능.

### B. 관리자용 자연어 분석 에이전트 (Admin Agent)
복잡한 SQL 쿼리나 대시보드 조작 없이, 자연어로 서비스 지표를 확인합니다.
- **도구(Tools)**:
    - `get_daily_active_users()`: 활성 사용자 수 조회
    - `get_problem_pass_rate(problem_id)`: 특정 문제의 정답률 및 주요 오답 패턴 조회
- **비즈니스 가치**: 관리 인력의 데이터 추출 업무를 AI가 대체하여 운영 효율성 증대.

### C. 외부 IDE 및 생태계 연동 (Headless Learning)
QueryCraft의 교육 콘텐츠를 MCP 리소스로 노출하여 외부 도구에서 QueryCraft를 사용할 수 있게 합니다.
- **리소스(Resources)**:
    - `problems/today`: 오늘의 연습 문제 데이터
    - `schema/all`: 전체 학습용 DB 스키마 정보
- **비즈니스 가치**: 사용자가 웹브라우저를 켜지 않고도 **Cursor IDE**나 **Claude Desktop**에서 바로 문제를 풀고 채점받는 환경 구축 가능.

## 3. 기대 효과
1. **정확도 향상**: AI가 추측이 아닌 실시간 데이터 정보를 바탕으로 응답.
2. **학습 경험 혁신**: 실제 실무 데이터 환경과 동일한 AI 피드백 제공.
3. **확장성**: 동일한 MCP 서버를 다양한 AI 클라이언트(Claude, Cursor 등)에서 재사용 가능.

## 4. 로드맵 (제안)
1. **Phase 1**: 백엔드에 `mcp-python-sdk` 설치 및 기본 DB 조회 도구 구현.
2. **Phase 2**: AI 힌트 및 피드백 기능에 MCP 도구 연동.
3. **Phase 3**: 관리자 전용 MCP 서버 구축 및 외부 IDE 연동 테스트.
