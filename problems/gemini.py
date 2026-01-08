# problems/gemini.py
from __future__ import annotations

import os
import json
import re
import time
import random
from datetime import datetime
from dotenv import load_dotenv
from google import genai

from backend.common.logging import get_logger

logger = get_logger(__name__)

load_dotenv()

# -------------------------------------------------
# Gemini Client & Multi-Model Support
# -------------------------------------------------
client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

# 용도별 모델 설정 (무료 티어 할당량 분산)
class GeminiModels:
    PROBLEM = os.getenv("GEMINI_MODEL_PROBLEM", "gemini-2.5-flash")      # 문제 생성
    GRADING = os.getenv("GEMINI_MODEL_GRADING", "gemini-2.5-flash")      # 채점
    TIPS = os.getenv("GEMINI_MODEL_TIPS", "gemini-2.5-flash-lite")       # 오늘의 팁 (경량)
    HINTS = os.getenv("GEMINI_MODEL_HINTS", "gemini-2.5-flash-lite")     # 힌트 (경량)
    ERROR = os.getenv("GEMINI_MODEL_ERROR", "gemini-3-flash")            # 에러 설명
    FALLBACK = "gemini-1.5-flash"                                         # 폴백

# 기본 모델 (호환성)
MODEL = os.getenv("GEMINI_MODEL", GeminiModels.PROBLEM)


def get_model_for_purpose(purpose: str) -> str:
    """용도에 맞는 모델 반환"""
    mapping = {
        "problem_generation": GeminiModels.PROBLEM,
        "grading": GeminiModels.GRADING,
        "grading_feedback": GeminiModels.GRADING,
        "tips": GeminiModels.TIPS,
        "hints": GeminiModels.HINTS,
        "error_explain": GeminiModels.ERROR,
    }
    return mapping.get(purpose, GeminiModels.FALLBACK)


# -------------------------------------------------
# API 사용량 로깅
# -------------------------------------------------
def log_api_usage(purpose: str, model: str, input_tokens: int = 0, output_tokens: int = 0, user_id: str = None):
    """Gemini API 사용량을 DB에 로깅"""
    try:
        from backend.services.database import postgres_connection
        with postgres_connection() as pg:
            pg.execute("""
                INSERT INTO public.api_usage_logs (purpose, model, input_tokens, output_tokens, total_tokens, user_id)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, [purpose, model, input_tokens, output_tokens, input_tokens + output_tokens, user_id])
        logger.info(f"API usage logged: {purpose}, model={model}, tokens={input_tokens + output_tokens}")
    except Exception as e:
        logger.error(f"Failed to log API usage: {e}")


def _call_gemini_with_retry(model: str, contents: str, purpose: str = "general", max_retries: int = 3):
    """Gemini API 호출 (503/429 발생 시 재시도 + 마지막에 모델 폴백)"""
    current_model = model
    
    for i in range(max_retries):
        try:
            return client.models.generate_content(model=current_model, contents=contents)
        except Exception as e:
            err_str = str(e)
            # 재시도 가능한 에러 체크 (503: Overloaded, 429: Rate Limit)
            if any(code in err_str for code in ["503", "429", "UNAVAILABLE", "ResourceExhausted"]) or "overloaded" in err_str.lower():
                # 2번째 재시도부터는 모델을 폴백 모델로 변경 시도
                if i >= 1 and current_model != GeminiModels.FALLBACK:
                    logger.warning(f"[GEMINI] High load detected. Falling back to {GeminiModels.FALLBACK}")
                    current_model = GeminiModels.FALLBACK
                
                wait_time = (2 ** i) + (random.random() * 2)
                logger.warning(f"[GEMINI] API Error ({purpose}, retry {i+1}/{max_retries}): {e}. Waiting {wait_time:.1f}s...")
                time.sleep(wait_time)
                continue
            
            logger.error(f"[GEMINI] Non-retryable API Error ({purpose}): {e}")
            raise e
            
    # 마지막 시도 (폴백 모델 강제 적용)
    logger.info(f"[GEMINI] Final attempt for {purpose} with {GeminiModels.FALLBACK}")
    return client.models.generate_content(model=GeminiModels.FALLBACK, contents=contents)


# -------------------------------------------------
# 1️⃣ 문제 출제용 (JSON 강제)
# -------------------------------------------------
def call_gemini_json(prompt: str, purpose: str = "problem_generation") -> list[dict]:
    logger.info(f"calling gemini for {purpose}")

    response = _call_gemini_with_retry(
        model=MODEL,
        contents=prompt,
        purpose=purpose
    )

    raw_text = response.text.strip()
    logger.debug(f"raw gemini response:\n{raw_text}")
    
    # 토큰 사용량 추정 (정확한 값은 response.usage_metadata에서)
    input_tokens = len(prompt) // 4  # 대략적 추정
    output_tokens = len(raw_text) // 4
    
    # 사용량 로깅
    log_api_usage(purpose=purpose, model=MODEL, input_tokens=input_tokens, output_tokens=output_tokens)

    # ------------------------------------------------
    # 1. ```json ... ``` 코드블록 우선 추출
    # ------------------------------------------------
    code_block = re.search(
        r"```(?:json)?\s*(.*?)\s*```",
        raw_text,
        re.DOTALL | re.IGNORECASE,
    )

    if code_block:
        json_text = code_block.group(1).strip()
    else:
        # ------------------------------------------------
        # 2. 코드블록이 없으면, JSON 배열/객체 직접 추출
        # ------------------------------------------------
        json_match = re.search(
            r"(\[\s*\{.*?\}\s*\]|\{.*?\})",
            raw_text,
            re.DOTALL,
        )
        if not json_match:
            logger.error("No JSON structure found in Gemini response")
            raise RuntimeError(f"Gemini 응답에서 JSON을 찾지 못했습니다:\n{raw_text}")

        json_text = json_match.group(1).strip()

    # ------------------------------------------------
    # 3. JSON 파싱
    # ------------------------------------------------
    try:
        return json.loads(json_text)
    except json.JSONDecodeError as e:
        logger.error("Gemini JSON parse failed")
        logger.error(f"extracted json text:\n{json_text}")
        raise RuntimeError(
            f"Gemini JSON 파싱 실패\n{json_text}"
        ) from e


# -------------------------------------------------
# 2️⃣ PA 채점용 (자연어 피드백)
# -------------------------------------------------
def grade_pa_submission(
    *,
    problem_id: str,
    sql_text: str,
    is_correct: bool,
    diff: str | None = None,
    error: str | None = None,
    note: str | None = None,
) -> str:
    """
    PA 제출 채점:
    - SQL 에러
    - 논리 오류
    - 실무 관점 피드백
    """

    logger.info(f"grading pa submission problem_id={problem_id}")

    # ---------------------------------------------
    # 프롬프트 구성
    # ---------------------------------------------
    prompt = f"""
너는 시니어 데이터 분석가다.
아래는 실무 PA(제품 분석) SQL 과제의 제출 결과다.

[문제 ID]
{problem_id}

[사용자 SQL]
{sql_text}

[사용자 메모]
{note or "없음"}

[실행 결과 요약]
- 정답 여부: {"정답" if is_correct else "오답"}
- SQL 에러: {error or "없음"}
- 결과 차이: {diff or "없음"}

[채점 기준]
1. SQL 문법 오류가 있다면 그것을 먼저 지적한다.
2. 논리적으로 왜 틀렸는지 또는 왜 맞았는지 설명한다.
3. 실무에서 더 좋은 접근이나 보완할 점을 제안한다.
4. 정답이어도 개선 포인트가 있으면 반드시 언급한다.
5. 불필요한 장황한 설명은 피하고, 실무 피드백 톤으로 작성한다.

[출력 형식]
- 자연어 텍스트
- 항목별로 명확하게 구분
"""

    # ---------------------------------------------
    # Gemini 호출
    # ---------------------------------------------
    response = _call_gemini_with_retry(
        model=MODEL,
        contents=prompt,
        purpose="grading_feedback"
    )

    feedback = response.text.strip()
    
    # 사용량 로깅
    input_tokens = len(prompt) // 4
    output_tokens = len(feedback) // 4
    log_api_usage(purpose="grading_feedback", model=MODEL, input_tokens=input_tokens, output_tokens=output_tokens)

    logger.info("gemini grading completed")

    return feedback
