import os
import requests
import json
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
api_key = os.getenv("OPENROUTER_API_KEY")

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://ai-content-analyzer.local",
    "X-Title": "AI Content Analyzer",
}

models = [
    "openrouter/free",
    "nousresearch/hermes-3-llama-3.1-405b:free"
]

for model in models:
    print(f"Testing {model}...")
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Hello, how are you?"}],
        "max_tokens": 10,
    }
    
    resp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
    print(f"Status: {resp.status_code}")
    print(f"Headers: Retry-After={resp.headers.get('Retry-After')}, x-ratelimit-limit={resp.headers.get('x-ratelimit-limit')}, x-ratelimit-remaining={resp.headers.get('x-ratelimit-remaining')}")
    try:
        print(f"Body: {json.dumps(resp.json(), indent=2)}")
    except:
        print(f"Raw body: {resp.text}")
    print("-" * 50)
