
from google import genai
import os

# 1. API 키 설정 (직접 입력 또는 환경 변수)
API_KEY = "AIzaSyDP3upUsNFPrh3LEmJFT6Ynz2imbk9YStI" # 발급받은 키를 여기에 넣으세요

client = genai.Client(api_key=API_KEY)

print(f"{'모델 ID (name)':<40} | {'표시 이름 (display_name)'}")
print("-" * 80)

try:
    # 최신 SDK에서는 model 객체의 속성이 name, display_name 등으로 구성됩니다.
    for model in client.models.list():
        # 텍스트 생성이 가능한 모델인지 확인 (supported_actions 사용)
        if 'generate_content' in model.supported_actions:
            print(f"{model.name:<40} | {model.display_name}")
except Exception as e:
    print(f"오류 발생: {e}")
    # 만약 위 코드가 또 에러난다면, 아래 코드로 모든 속성을 확인해보세요.
    # print(model) 