# QueryCraft 서비스 구조 개편안 (2-Track Strategy)

> **핵심 컨셉**: "현재의 전문가(Expert)"와 "미래의 개척자(Pioneer)"를 동시에 양성하는 이원화된 경험 제공

---

## 1. 구조 개편 개요

기존에 산재되어 있던 기능들을 두 가지 명확한 트랙으로 분류하여 사용자에게 제공합니다.

| 구분 | **Track A: Core Skills (현재)** | **Track B: Future Lab (미래)** |
|:---:|:---|:---|
| **컨셉** | *"지금 당장 필요한 실무 역량의 완성"* | *"AI 시대 분석가가 일하는 방식의 미리보기"* |
| **목표** | SQL 숙련도, 데이터 문해력, 리포팅 기본기 | AI 협업, 의사결정 설계, 자동화 도구 활용 |
| **주요 기능** | PA/Stream 문제, Practice, Leaderboard | Text-to-SQL, AI Insight, RCA 시나리오, MCP |
| **사용자 경험** | Hard Training (반복, 숙달) | Advanced Simulation (실험, 탐구) |

---

## 2. 상세 메뉴 구성

### 🏢 Track A: Core Skills (Expert Mode)
> **"탄탄한 기본기가 최고의 무기입니다."**

기존 QueryCraft의 핵심 학습 기능들을 모아놓은 공간입니다.

1.  **Daily Training (일일 훈련)**
    *   `PA (Product Analytics)`: 매일 생성되는 지표 분석 SQL 문제
    *   `Stream`: 대용량 로그 데이터 처리 연습 (DuckDB)
2.  **Practice Arena (무한 연습)**
    *   토픽별/난이도별 SQL 문제 반복 풀이
    *   오답 노트 및 약점 보완
3.  **Data Center (데이터 센터)**
    *   가상 회사의 스키마 탐색 (`schema_viewer`)
    *   데이터 구조 이해 및 ERD 확인
4.  **Leaderboard (경쟁)**
    *   사용자 간 실력 비교 및 동기 부여

### 🚀 Track B: Future Lab (Pioneer Mode)
> **"AI와 함께 일하는 당신의 미래를 먼저 경험하세요."**

AI 기술이 접목된 분석 환경을 시뮬레이션하는 공간입니다.

1.  **AI Workspace (지능형 작업실)**
    *   `Natural Language Query`: 자연어로 SQL 초안 생성 및 수정 (Text-to-SQL)
    *   `Smart Insight`: 쿼리 결과에서 자동으로 비즈니스 인사이트 도출
2.  **Crisis Simulator (RCA 시나리오)**
    *   "매출 급감", "전환율 하락" 등 가상의 위기 상황 시뮬레이션
    *   AI가 생성한 복잡한 시나리오의 원인 규명
3.  **MCP Sandbox (연동 실험실)**
    *   실시간 DB 연동 AI 에이전트 체험
    *   AI가 데이터 존재 여부와 쿼리 성능을 미리 체크해주는 경험
4.  **Adaptive Tutor (맞춤형 멘토)**
    *   나의 성향과 약점을 분석해주는 AI 분석가 리포트

---

## 3. UI/UX 디자인 방향성

### 네비게이션 (GNB)
*   좌측 상단에 명확한 **모드 전환 스위치 (Toggle/Tab)** 배치
*   **Track A** 선택 시: 차분하고 전문적인 `Blue/Grey` 톤 (IDE 느낌)
*   **Track B** 선택 시: 혁신적이고 미래지향적인 `Purple/Neon` 톤 (AI Lab 느낌)

### 온보딩 메시지
*   **Track A 진입 시**: "오늘도 실전 감각을 유지하세요. 3개의 문제가 기다리고 있습니다."
*   **Track B 진입 시**: "2026년의 분석 환경에 오신 것을 환영합니다. AI 파트너가 준비되었습니다."

---

## 4. 기대 효과

1.  **목적성 명확화**: 사용자가 '학습'을 하러 왔는지, '새로운 경험'을 하러 왔는지에 따라 최적의 동선 제공
2.  **가치 제안 강화**: 단순 SQL 문제 은행이 아니라, "미래 준비"까지 가능한 커리어 플랫폼으로 포지셔닝
3.  **기능 확장 용이성**: 신규 AI 기능은 Future Lab에, 기본 문제는 Core Skills에 추가하여 복잡도 관리

---

*이 문서는 서비스 개편의 청사진으로 사용됩니다.*
