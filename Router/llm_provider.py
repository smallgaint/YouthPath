from __future__ import annotations

import json
import os
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import requests


class LLMProvider(ABC):
    @abstractmethod
    def invoke(self, prompt: str, **kwargs: Any) -> str:
        raise NotImplementedError


def get_llm_provider() -> LLMProvider:
    """Return the configured provider.

    Set YOUTHPATH_LLM_PROVIDER=luxia and fill LUXIA_API_URL/LUXIA_API_KEY
    when the real LUXIA contract is available. Without those values the app
    stays on MockLuxiaProvider so local E2E remains runnable.
    """
    _load_env_file()
    provider_name = os.getenv("YOUTHPATH_LLM_PROVIDER", "auto").strip().lower()
    luxia_url = os.getenv("LUXIA_API_URL", "").strip()
    luxia_key = os.getenv("LUXIA_API_KEY", "").strip()

    if provider_name == "mock":
        return MockLuxiaProvider()
    if provider_name in {"luxia", "auto"} and luxia_url and luxia_key:
        return LuxiaProvider()
    return MockLuxiaProvider()


class LuxiaProvider(LLMProvider):
    def __init__(
        self,
        *,
        api_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        timeout: float | None = None,
        fallback_provider: LLMProvider | None = None,
    ):
        _load_env_file()
        self.api_url = api_url or os.getenv("LUXIA_API_URL", "").strip()
        self.api_key = api_key or os.getenv("LUXIA_API_KEY", "").strip()
        self.model = model or os.getenv("LUXIA_MODEL", "luxia").strip()
        self.timeout = timeout or float(os.getenv("LUXIA_TIMEOUT", "60"))
        self.request_format = os.getenv("LUXIA_REQUEST_FORMAT", "openai").strip().lower()
        self.auth_header = os.getenv("LUXIA_AUTH_HEADER", "apikey").strip()
        self.auth_scheme = os.getenv("LUXIA_AUTH_SCHEME", "").strip()
        self.include_generation_params = (
            os.getenv("LUXIA_INCLUDE_GENERATION_PARAMS", "false").strip().lower() == "true"
        )
        self.fallback_to_mock = os.getenv("LUXIA_FALLBACK_TO_MOCK", "true").strip().lower() != "false"
        self.fallback_provider = fallback_provider or MockLuxiaProvider()

        if not self.api_url:
            raise ValueError("LUXIA_API_URL is required for LuxiaProvider.")
        if not self.api_key:
            raise ValueError("LUXIA_API_KEY is required for LuxiaProvider.")

    def invoke(self, prompt: str, **kwargs: Any) -> str:
        payload = self._build_payload(prompt, **kwargs)
        headers = self._build_headers()
        started = time.perf_counter()
        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            return self._extract_text(data)
        except Exception as exc:  # noqa: BLE001
            if self.fallback_to_mock:
                fallback = self.fallback_provider.invoke(prompt, **kwargs)
                return fallback
            raise RuntimeError(f"LUXIA request failed after {time.perf_counter() - started:.2f}s: {exc}") from exc

    def _build_payload(self, prompt: str, **kwargs: Any) -> dict[str, Any]:
        purpose = kwargs.get("purpose", "general")
        temperature = kwargs.get("temperature", 0.1 if purpose == "classification" else 0.4)
        max_tokens = kwargs.get("max_tokens", 512 if purpose == "classification" else 1200)

        if self.request_format == "generic":
            return {
                "model": self.model,
                "prompt": prompt,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "metadata": {"purpose": purpose},
            }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are YouthPath's Korean assistant. Follow the requested output format exactly.",
                },
                {"role": "user", "content": prompt},
            ],
            "stream": False,
        }
        if self.include_generation_params:
            payload["temperature"] = temperature
            payload["max_tokens"] = max_tokens
        return payload

    def _build_headers(self) -> dict[str, str]:
        auth_value = self.api_key
        if self.auth_scheme:
            auth_value = f"{self.auth_scheme} {self.api_key}"
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            self.auth_header: auth_value,
        }

    def _extract_text(self, data: Any) -> str:
        if isinstance(data, str):
            return data
        if not isinstance(data, dict):
            return str(data)

        choices = data.get("choices")
        if isinstance(choices, list) and choices:
            first = choices[0]
            if isinstance(first, dict):
                message = first.get("message")
                if isinstance(message, dict) and message.get("content"):
                    return str(message["content"])
                if first.get("text"):
                    return str(first["text"])

        for key in ["output_text", "answer", "content", "text", "result", "response"]:
            value = data.get(key)
            if isinstance(value, str) and value:
                return value
            if isinstance(value, dict):
                nested = self._extract_text(value)
                if nested:
                    return nested

        raise ValueError(f"Cannot extract LUXIA text from response keys: {sorted(data.keys())}")


class MockLuxiaProvider(LLMProvider):
    def invoke(self, prompt: str, **kwargs: Any) -> str:
        prompt_lower = prompt.lower()
        if "agents" in prompt_lower or "분류" in prompt_lower:
            agents: list[str] = []
            policy_keywords = ["정책", "지원금", "월세", "복지", "청년", "주거", "수당", "장학"]
            job_keywords = ["채용", "공고", "취업", "직무", "회사", "신입", "경력", "일자리"]
            resume_keywords = ["이력서", "자소서", "자기소개서", "지원동기", "기업 분석", "포트폴리오"]
            calendar_keywords = ["마감", "일정", "캘린더", "deadline", "d-day"]

            if any(keyword in prompt_lower for keyword in policy_keywords):
                agents.append("policy")
            if any(keyword in prompt_lower for keyword in job_keywords):
                agents.append("job")
            if any(keyword in prompt_lower for keyword in resume_keywords):
                agents.append("resume")
            if any(keyword in prompt_lower for keyword in calendar_keywords):
                agents.append("calendar")
            if "target_company" in prompt_lower or "관심 기업" in prompt_lower:
                if "resume" not in agents:
                    agents.append("resume")
            if not agents:
                agents = ["policy", "job"]

            return json.dumps(
                {"agents": agents, "reasoning": "mock luxia keyword classification"},
                ensure_ascii=False,
            )
        return "[MOCK_LUXIA] LUXIA API 계약 전까지 mock provider가 에이전트 결과를 통합했습니다."


def _load_env_file() -> None:
    candidates = [
        Path.cwd() / ".env",
        Path(__file__).resolve().parent.parent / ".env",
    ]
    env_path = next((path for path in candidates if path.exists()), None)
    if env_path is None:
        return
    try:
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value
    except Exception:
        return
