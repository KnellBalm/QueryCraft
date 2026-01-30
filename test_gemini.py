import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
model_name = os.getenv("GEMINI_MODEL_PROBLEM", "gemini-flash-latest")

print(f"Testing with Model: {model_name}")

try:
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model_name,
        contents="Hello, tell me a short joke about SQL."
    )
    print("Success!")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Failure: {e}")
