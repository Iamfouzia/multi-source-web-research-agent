import os
import requests
from dotenv import load_dotenv

load_dotenv()

base_url = os.environ.get("GROK_BASE_URL", "")
model = os.environ.get("GROK_MODEL", "")
key = os.environ.get("GROK_API_KEY", "")

print("BASE_URL:", repr(base_url))
print("MODEL:", repr(model))
print("KEY starts with:", key[:8], "len:", len(key))

url = base_url.rstrip("/") + "/chat/completions"
print("FULL URL:", url)

r = requests.post(
    url,
    headers={"Authorization": f"Bearer {key}"},
    json={"model": model, "messages": [{"role": "user", "content": "hi"}]},
)
print("STATUS:", r.status_code)
print("BODY:", r.text)


print("\n--- Listing available models for this key ---")
list_url = base_url.rstrip("/") + "/models"
r2 = requests.get(list_url, headers={"Authorization": f"Bearer {key}"})
print("LIST STATUS:", r2.status_code)
print("LIST BODY:", r2.text[:2000])