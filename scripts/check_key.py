import os
from dotenv import load_dotenv
load_dotenv()
key = os.getenv("GEMINI_API_KEY")
if key:
    print(f"Key loaded: {key[:4]}...{key[-4:]}")
    print(f"Key length: {len(key)}")
else:
    print("Key not found in env")
