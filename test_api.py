import requests
import json
import os

url = "https://router.huggingface.co/v1/chat/completions"
token = os.environ.get("HF_TOKEN", "")

if not token:
    raise RuntimeError("HF_TOKEN is not set. Export HF_TOKEN before running this script.")

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}
data = {
    "model": "meta-llama/Llama-3-8b-chat-hf",
    "messages": [{"role": "user", "content": "Hi"}]
}

resp = requests.post(url, headers=headers, json=data)
print("Status Code:", resp.status_code)
print("Response:", resp.text)
