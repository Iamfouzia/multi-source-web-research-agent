import requests

from research_agent.retry import call_with_retries


class GrokClient:
    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model

    def complete(self, system_prompt: str, user_prompt: str, timeout: int = 30, max_retries: int = 2) -> str:
        def _call() -> str:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.2,
                },
                timeout=timeout,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

        return call_with_retries(_call, max_retries=max_retries, retry_on=(requests.RequestException,))
