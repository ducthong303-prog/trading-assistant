import requests
import os

API_KEY = os.environ.get("DEEPSEEK_API_KEY")

def chat(message, model="deepseek-v4-pro"):
    response = requests.post(
        "https://api.deepseek.com/chat/completions",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": model,
            "messages": [{"role": "user", "content": message}]
        }
    )
    data = response.json()
    return data["choices"][0]["message"]["content"]

# Test
print(chat("Xin chào! Bạn là model gì?"))
