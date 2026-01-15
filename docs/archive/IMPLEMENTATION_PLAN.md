# RCA (Root Cause Analysis) 모드 구현 계획

## 1. 개요
비즈니스 지표의 이상 현상(Anomaly)을 탐지하고 그 원인을 분석하는 RCA 모드를 추가함. 기존 PA(Product Analytics) 모드와 차별화된 시나리오와 UI를 제공.

## 2. 변경 사항

### 백엔드 (Backend)
- **프롬프트 엔지니어링**: `problems/prompt_rca.py` 추가. 지표 하락/상승 시나리오와 데이터 기반 원인 분석(Deep-dive) 문제 생성 로직 구현.
- **문제 생성 엔진**: `problems/generator.py` 수정. `mode` 파라미터 도입하여 `pa`, `rca`, `stream` 모드 지원. 파일명 및 DB 저장 시 모드 구분.
- **API**: `backend/api/problems.py` 수정. `rca` 데이터 타입 지원 및 스키마/메타데이터 연동.
- **스케줄러**: `backend/scheduler.py` 수정. 평일 작업 시 PA와 RCA 문제를 각각 생성하고 기록하도록 업데이트.

### 프론트엔드 (Frontend)
- **네비게이션**: 상단 GNB 및 메인 페이지에 'RCA 분석' 메뉴 추가.
- **워크스페이스**: `rca` 모드 시 'ABNORMALITY DETECTED' 배지, 리얼타임 느낌의 아이콘, 강조된 UI 요소 추가.
- **관리자**: 관리자 페이지에서 RCA 문제를 수동으로 생성할 수 있는 버튼 추가.

## 3. 검증 계획
- `scripts/test_rca_gen.py`를 통한 문제 생성 품질 확인.
- 프론트엔드 RCA 메뉴 진입 및 문제 로드 확인.
- 스케줄러 자동 실행 로그 확인.
