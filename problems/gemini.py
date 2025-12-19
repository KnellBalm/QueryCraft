# problems/gemini.py
from __future__ import annotations
import os
import json
from google import genai
from dotenv import load_dotenv
from common.logging import get_logger
logger = get_logger(__name__)

load_dotenv()


client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.0-pro")

def call_gemini_json(prompt: str) -> list[dict]:
    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
    )

    text = response.text.strip()

    # ```json 제거
    if text.startswith("```"):
        text = text.split("```")[1]

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"Gemini JSON 파싱 실패\n{text}"
        ) from e
