"""Ollama 로컬 LLM 호출 래퍼."""

import os
import re

import requests

from .config import load_dotenv

load_dotenv()

OLLAMA_HOST = (
    os.environ.get("OLLAMA_HOST")
    or os.environ.get("OLLAMA_URL")
    or "http://localhost:11434"
)
OLLAMA_MODEL = (
    os.environ.get("OLLAMA_MODEL")
    or os.environ.get("GENERATE_MODEL")
    or "gemma4:e4b"
)
REQUEST_TIMEOUT_SECONDS = 120

_CODE_FENCE_RE = re.compile(r"^```(?:sql)?\s*|\s*```$", re.IGNORECASE | re.MULTILINE)


def _extract_sql(raw_text: str) -> str:
    """모델 출력에서 SQL 텍스트만 뽑아낸다 (코드펜스 제거, 앞뒤 공백 정리)."""
    text = _CODE_FENCE_RE.sub("", raw_text).strip()
    return text


def generate_sql(prompt: str) -> str:
    """Ollama /api/generate 를 호출해 SQL 문자열을 반환한다."""
    response = requests.post(
        f"{OLLAMA_HOST}/api/generate",
        json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0},
        },
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    raw_text = response.json()["response"]
    return _extract_sql(raw_text)
