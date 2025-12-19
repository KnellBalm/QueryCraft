from problems.gemini import call_gemini_json

prompt = """
아래 요구사항을 만족하는 JSON을 만들어라.

[
  {
    "task_id": "TEST_01",
    "domain": "marketing",
    "difficulty": "easy",
    "context": "테스트용 Gemini 호출 검증",
    "request": ["이 문장은 테스트다"],
    "constraints": ["없음"],
    "deliverables": ["JSON이 잘 내려오는지 확인"]
  }
]

JSON만 출력하라.
"""

result = call_gemini_json(prompt)

print("Gemini response:")
print(result)
