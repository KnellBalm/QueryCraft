# Mixpanel KPI Tree & Tracking Plan (SQL Problem Service)

## 1. 북극성 지표 (North Star Metric)

### 1.1 초기 단계 (수요 검증)
- **Daily Solved Problems**: 하루 동안 발생한 전체 `Problem Solved` 수

### 1.2 성장 단계 (유저 활성화)
- **Solved DAU**: 하루 동안 문제를 1회 이상 해결한 고유 유저 수

---

## 2. KPI 트리 구조

- **Solved DAU** (NSM)
  - **DAU** (유입 지표)
    - 신규 유입 (`Sign Up Completed`)
    - 기존 유저 유지 (`Login Success`)
  - **Solved Rate** (전환 지표)
    - 시도율 (`Problem Attempted` / `Problem Viewed`)
    - 정답률 (`Problem Solved` / `Problem Attempted`)
  - **Friction** (방해 지표)
    - SQL 에러율 (`SQL Error Occurred` / `SQL Executed`)
    - 힌트 의존도 (`Hint Requested` / `Problem Attempted`)
  - **Retention** (유지 지표)
    - 

---

## 3. 트래킹 명세 (Tracking Plan)

### 3.1 핵심 유저 여정 (Funnel)
1. **Problem Viewed**: 문제 상세 페이지 진입
2. **Problem Attempted**: 첫 쿼리 타이핑 또는 실행 시점
3. **Problem Submitted**: 제출 버튼 클릭
4. **Problem Solved**: 정답 판정 (최종 목적지)

### 3.2 이벤트 상세 속성

| 이벤트 명 | 트리거 시점 | 필수 속성 |
| :--- | :--- | :--- |
| **Problem Viewed** | 문제 페이지 로드 | `problem_id`, `difficulty_level`, `is_daily_problem`, `data_type` |
| **Problem Attempted** | 첫 쿼리 편집/실행 | `problem_id`, `difficulty_level`, `attempt_count` |
| **SQL Executed** | 실행 버튼 클릭 | `problem_id`, `sql_length`, `db_engine` |
| **SQL Error Occurred**| 실행 에러 발생 | `error_type`, `error_message`, `sql_text` |
| **Problem Submitted** | 제출 버튼 클릭 | `problem_id`, `attempt_count`, `result` |
| **Problem Solved** | 정답 판정 | `problem_id`, `attempt_count`, `time_spent_sec`, `difficulty_level` |
| **Hint Requested** | 힌트 버튼 클릭 | `problem_id`, `hint_type` |

### 3.3 공통 속성
- `problem_id`: 문제 식별자
- `difficulty_level`: easy, medium, hard
- `is_daily_problem`: 오늘의 문제 여부 (boolean)
- `attempt_count`: 현재 문제에서의 시도 횟수
- `time_spent_sec`: 문제 진입 후 해결까지 소요 시간

---

## 4. 분석 리포트 설계
- **Funnel Report**: 주요 이탈 구간 파악 (View -> Attempt -> Solve)
- **Retention Report**: 문제 해결 기반의 재방문 측정
- **Friction Insight**: 에러 유형별 발생 빈도 및 힌트 사용 시 정답률 변화 분석

---

## 5. Mixpanel Lexicon 관리

이벤트와 속성의 한글 표시 이름 및 설명을 일괄 관리하기 위해 Lexicon CSV 파일을 사용합니다.

### 5.1 Lexicon 적용 방법
1. 믹스패널 **Data Management > Lexicon** 접속
2. **Events** 탭 선택 -> **Import** 클릭 -> [mixpanel_final_events.csv](../docs/mixpanel_final_events.csv) 업로드
3. **Event Properties** 탭 선택 -> **Import** 클릭 -> [mixpanel_final_properties.csv](../docs/mixpanel_final_properties.csv) 업로드

### 5.2 Lexicon 데이터 파일 설명
- [mixpanel_final_events.csv](../docs/mixpanel_final_events.csv): 이벤트 명칭 및 메타데이터 (24컬럼 규격)
- [mixpanel_final_properties.csv](../docs/mixpanel_final_properties.csv): 속성 명칭 및 타입 정보 (24컬럼 규격)

### 5.3 데이터 갱신 및 관리 (Python)
트래킹 계획이 변경되어 CSV를 다시 생성해야 할 경우, 프로젝트 루트에서 아래 스크립트 로직을 참고하십시오.

```python
# Lexicon CSV 생성 로직 요약
import csv

header = ["Entity Type", "Entity Name", "Entity Display Name", "Entity Description", ...] # 총 24개 컬럼

# 이벤트/속성 데이터를 정의한 후 규격에 맞춰 CSV 저장
# 상세 코드는 개발팀 가이드 참고
```
