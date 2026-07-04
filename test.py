"""Minimal DeepSeek smoke test.

Set DEEPSEEK_API_KEY in your shell environment before running.
Optionally set DEEPSEEK_BASE_URL to override the default endpoint.
"""

import os

from langchain_openai import OpenAI


api_key = os.environ.get("DEEPSEEK_API_KEY")
if not api_key:
    raise RuntimeError(
        "DEEPSEEK_API_KEY is not set. Export it before running this script."
    )

llm = OpenAI(
    api_key=api_key,
    base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
)

res = llm.invoke("什么是人工智能？")
print(res)
