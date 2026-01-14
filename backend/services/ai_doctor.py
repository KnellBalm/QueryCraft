# backend/services/ai_doctor.py
"""
AI Doctor - 시스템 가동 진단 및 자동 복구 서비스
에러 발생 시 Gemini를 사용하여 원인을 분석하고 가능한 경우 자가 복구를 시도합니다.
"""
import os
import traceback
from typing import Dict, Any, List
from backend.common.logging import get_logger
from problems.gemini import _call_gemini_with_retry
from backend.services.notification_service import send_email

logger = get_logger(__name__)

class AIDoctor:
    def __init__(self):
        self.model = os.getenv("GEMINI_MODEL_ERROR", "gemini-1.5-flash")

    def diagnose_and_heal(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        에러를 진단하고 가능한 경우 복구 조치를 제안하거나 실행합니다.
        """
        error_str = str(error)
        stack_trace = traceback.format_exc()
        
        logger.info(f"[AI Doctor] Diagnosing error: {error_str[:100]}...")

        # 1. Gemini에게 분석 및 처방 요청
        diagnosis = self._get_ai_diagnosis(error_str, stack_trace, context)
        
        # 2. 분석 결과에 따른 조치 실행 (Safe Actions only)
        recovery_result = self._attempt_recovery(diagnosis.get("action"))
        
        # 3. 종합 보고서 작성
        report = {
            "root_cause": diagnosis.get("root_cause", "알 수 없는 원인"),
            "severity": diagnosis.get("severity", "Medium"),
            "action_taken": diagnosis.get("action_message", "조치 없음"),
            "recovery_status": recovery_result.get("status", "N/A"),
            "recommendation": diagnosis.get("recommendation", "매뉴얼 확인 필요")
        }
        
        return report

    def _get_ai_diagnosis(self, error: str, stack_trace: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Gemini를 호출하여 에러 분석"""
        prompt = f"""
너는 'QueryCraft'라는 SQL 교육 플랫폼의 시스템 가동 진단 전문 AI다.
아래는 시스템 스케줄러 실행 중 발생한 에러 정보와 컨텍스트다.

[에러 메시지]
{error}

[스택 트레이스]
{stack_trace}

[실행 컨텍스트]
{context}

[요구사항]
1. 원인을 분석하고 실무적인 관점에서 해결책을 제시하라.
2. 아래 action 중 하나를 선택하라:
   - "RETRY_ONLY": 단순히 한 번 더 실행하면 될 것 같음 (네트워크 일시 오류 등)
   - "CLEANUP_AND_RETRY": 임시 파일이나 DB 상태를 정리하고 재시도 필요
   - "NOTIFY_ADMIN": 즉각적인 사람의 개입이 필요함 (API 키 만료, DB 다운 등)
   - "IGNORE_AND_PROCEED": 사소한 에러이므로 진행 가능

[출력 형식 (JSON)]
{{
  "root_cause": "원인 설명",
  "severity": "High/Medium/Low",
  "action": "ACTION_CODE",
  "action_message": "어떤 조치를 취할지 설명",
  "recommendation": "관리자에게 주는 권장사항"
}}
        """
        
        try:
            import json
            response = _call_gemini_with_retry(model=self.model, contents=prompt, purpose="doctor_diagnosis")
            # JSON만 추출 (필요 시 마크다운 제거)
            content = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(content)
        except Exception as e:
            logger.error(f"AI Doctor Gemini 호출 실패: {e}")
            return {
                "root_cause": f"AI 분석 실패 ({error})",
                "action": "NOTIFY_ADMIN",
                "action_message": "AI 분석 중 오류가 발생하여 수동 확인이 필요합니다."
            }

    def _attempt_recovery(self, action: str) -> Dict[str, Any]:
        """안전한 범위 내에서 자동 복구 시도"""
        if action == "RETRY_ONLY":
            return {"status": "자동 재시도 예약 (다음 주기에 시도)"}
        elif action == "CLEANUP_AND_RETRY":
            return {"status": "환경 정리 후 재시도 필요 (구현 예정)"}
        return {"status": "수동 조치 필요"}

def send_doctor_report(report: Dict[str, Any], date: str):
    """진단 보고서를 이메일로 발송"""
    subject = f"🛑 시스템 장애 진단 및 복구 보고서 ({date})"
    body = f"""AI Doctor가 시스템 장애를 감지하고 분석했습니다.

[진단 결과]
- 원인: {report['root_cause']}
- 위험도: {report['severity']}

[수행된 조치]
- {report['action_taken']}
- 상태: {report['recovery_status']}

[권장 사항]
{report['recommendation']}

---
본 보고서는 AI에 의해 자동으로 생성되었습니다.
    """
    send_email(subject, body)
