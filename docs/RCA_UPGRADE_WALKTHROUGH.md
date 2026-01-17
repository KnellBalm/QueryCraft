# Walkthrough: RCA 시나리오 고도화

RCA(원인 분석) 시나리오를 실무 레벨로 끌어올리기 위한 백엔드 및 프론트엔드 통합 고도화 작업을 완료했습니다.

## 주요 변경 사항

### 1. 백엔드 (Backend)
- **장애 시나리오 고도화**: `anomaly_injector.py`를 수정하여 단순한 데이터 주입을 넘어, 장애의 원인과 분석 방향을 포함하는 상세 메타데이터를 생성합니다.
  - 신규 시나리오: `RETENTION_DROP` (리텐션 급락), `CONVERSION_DROP` (가입 전환 하락), `CHANNEL_INEFFICIENCY` (특정 채널 효율 저하)
- **AI 프롬프트 연동**: `prompt_rca.py` 및 `prompt.py`를 개선하여 주입된 이상 패턴 메타데이터를 Gemini가 인식하고, 분석 단계를 안내하는 **단계별 힌트(Sequential Hints)**를 생성하도록 했습니다.
- **관리자 API**: `/admin/trigger-rca` 엔드포인트를 추가하여 특정 장애 시나리오를 수동으로 발생시키고 관련 문제를 즉시 생성할 수 있습니다.

### 2. 프론트엔드 (Frontend)
- **Anomaly Briefing**: 문제 목록 패널상단에 데이터상의 이상 징후를 요약해서 보여주는 섹션을 추가했습니다.
- **Step-by-Step Hint System**: 정답을 바로 알려주는 대신, "이 지표를 먼저 확인해보세요", "그 다음엔 이 테이블을 조인해보세요"와 같이 사고 과정을 가이드하는 아코디언 타입 힌트 시스템을 구현했습니다.
- **Analysis Report Template**: 분석을 마친 사용자가 결과를 구조화할 수 있도록 표준 RCA 리포트 템플릿(Markdown)을 클립보드에 복사해주는 기능을 추가했습니다.

## 스크린샷 및 검증

### 🎨 UI 개선 사항
- **단계별 힌트**: `Workspace.css`를 통해 프리미엄 디자인이 적용된 아코디언 UI를 구현했습니다.
- **리포트 템플릿 버튼**: 결과 패널 하단에 RCA 모드에서만 활성화되는 전용 버튼을 배치했습니다.

### 🧪 내부 로직 검증
- `tests/test_rca_trigger.py`를 통해 이상 주입 -> 문제 생성 -> 단계별 힌트 포함 여부를 검증했습니다.

```python
# 검증 결과 예시
--- Internal RCA Trigger Test ---
Injecting anomaly for 2026-01-18...
Injected: RETENTION_DROP
Generating RCA problems...
Problems generated at: problems/daily/rca_2026-01-18.json
Found 3 problems.
Problem 1 title: 리텐션 급락 원인 분석 (Ver. 1.0)
Hints: ['1단계: 일자별 리텐션 추이를 먼저 확인해보세요.', '2단계: 특정 가입 채널에서 유독 하락이 큰지 분석해보세요.', ...]
SUCCESS: Hints generated correctly.
```

## 향후 계획
- **AI 인사이트 리포트**: 사용자가 작성한 쿼리 결과를 AI가 자동으로 해석하여 요약해주는 기능을 추가할 예정입니다.
- **MCP 연동**: 외부 IDE에서도 이 분석 환경에 바로 접근할 수 있도록 인프라를 확장할 계획입니다.
