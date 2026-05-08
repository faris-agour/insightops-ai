import json
import os
from abc import ABC, abstractmethod
from typing import Any


class LLMProviderError(RuntimeError):
    pass


class LLMProvider(ABC):
    @abstractmethod
    def send_decision_request(
        self, query: str, system_prompt: str, model: str, timeout_seconds: float
    ) -> dict[str, Any]:
        """
        Send a decision request to the LLM provider and return parsed JSON response.
        Must raise LLMProviderError on any failure.
        """
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """Check if the provider has required API keys configured."""
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Return the provider name for logging."""
        pass


class GroqProvider(LLMProvider):
    DEFAULT_API_URL = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(self) -> None:
        self.api_key = os.getenv("GROQ_API_KEY", "").strip()
        self.api_url = os.getenv("GROQ_API_URL", self.DEFAULT_API_URL).strip() or self.DEFAULT_API_URL

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def get_name(self) -> str:
        return "Groq"

    def send_decision_request(
        self, query: str, system_prompt: str, model: str, timeout_seconds: float
    ) -> dict[str, Any]:
        if not self.is_configured():
            raise LLMProviderError("GROQ_API_KEY is not configured")

        try:
            import requests
        except ImportError as exc:
            raise LLMProviderError("requests library is required") from exc

        payload = {
            "model": model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query},
            ],
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(
                self.api_url, json=payload, headers=headers, timeout=timeout_seconds
            )
            response.raise_for_status()
            response_json = response.json()
        except requests.Timeout as exc:
            raise LLMProviderError(f"{self.get_name()} request timed out") from exc
        except requests.RequestException as exc:
            raise LLMProviderError(f"{self.get_name()} request failed: {str(exc)}") from exc
        except ValueError as exc:
            raise LLMProviderError(f"{self.get_name()} response is not valid JSON") from exc

        return self._extract_openai_response(response_json)

    def _extract_openai_response(self, response_json: dict[str, Any]) -> dict[str, Any]:
        choices = response_json.get("choices")
        if not isinstance(choices, list) or not choices:
            raise LLMProviderError(f"{self.get_name()} response has no choices")

        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            raise LLMProviderError(f"{self.get_name()} response choice format is invalid")

        message = first_choice.get("message", {})
        if not isinstance(message, dict):
            raise LLMProviderError(f"{self.get_name()} response message format is invalid")

        content = message.get("content", "")
        if isinstance(content, str):
            return {"content": content}

        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if isinstance(item, dict):
                    text = item.get("text")
                    if text:
                        parts.append(str(text))
                elif isinstance(item, str):
                    parts.append(item)
            return {"content": "\n".join(parts)}

        raise LLMProviderError(f"{self.get_name()} response content is invalid")


class HuggingFaceProvider(LLMProvider):
    DEFAULT_API_URL = "https://api-inference.huggingface.co/models"
    DEFAULT_MODEL = "meta-llama/Llama-2-7b"

    def __init__(self) -> None:
        self.api_key = os.getenv("HF_API_KEY", "").strip()
        self.api_url = os.getenv("HF_API_URL", self.DEFAULT_API_URL).strip() or self.DEFAULT_API_URL
        self.model = os.getenv("HF_MODEL", self.DEFAULT_MODEL).strip() or self.DEFAULT_MODEL

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def get_name(self) -> str:
        return "HuggingFace"

    def send_decision_request(
        self, query: str, system_prompt: str, model: str, timeout_seconds: float
    ) -> dict[str, Any]:
        if not self.is_configured():
            raise LLMProviderError("HF_API_KEY is not configured")

        try:
            import requests
        except ImportError as exc:
            raise LLMProviderError("requests library is required") from exc

        full_prompt = f"{system_prompt}\n\nUser: {query}\n\nAssistant:"

        payload = {
            "inputs": full_prompt,
            "parameters": {
                "max_new_tokens": 1024,
                "temperature": 0.0,
            },
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        endpoint = f"{self.api_url}/{self.model}"

        try:
            response = requests.post(endpoint, json=payload, headers=headers, timeout=timeout_seconds)
            response.raise_for_status()
            response_json = response.json()
        except requests.Timeout as exc:
            raise LLMProviderError(f"{self.get_name()} request timed out") from exc
        except requests.RequestException as exc:
            raise LLMProviderError(f"{self.get_name()} request failed: {str(exc)}") from exc
        except ValueError as exc:
            raise LLMProviderError(f"{self.get_name()} response is not valid JSON") from exc

        return self._extract_hf_response(response_json)

    def _extract_hf_response(self, response_json: Any) -> dict[str, Any]:
        if isinstance(response_json, list) and response_json:
            response_json = response_json[0]

        if not isinstance(response_json, dict):
            raise LLMProviderError(f"{self.get_name()} response format is invalid")

        generated_text = response_json.get("generated_text", "")
        if not isinstance(generated_text, str):
            raise LLMProviderError(f"{self.get_name()} response missing generated_text")

        return {"content": generated_text}


class JetstreamProvider(LLMProvider):
    DEFAULT_API_URL = "https://api.jetstream.ai/v1/chat/completions"
    DEFAULT_MODEL = "gpt-oss-120b"

    def __init__(self) -> None:
        self.api_key = os.getenv("JETSTREAM_API_KEY", "").strip()
        self.api_url = os.getenv("JETSTREAM_API_URL", self.DEFAULT_API_URL).strip() or self.DEFAULT_API_URL
        self.model = os.getenv("JETSTREAM_MODEL", self.DEFAULT_MODEL).strip() or self.DEFAULT_MODEL

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def get_name(self) -> str:
        return "Jetstream"

    def send_decision_request(
        self, query: str, system_prompt: str, model: str, timeout_seconds: float
    ) -> dict[str, Any]:
        if not self.is_configured():
            raise LLMProviderError("JETSTREAM_API_KEY is not configured")

        try:
            import requests
        except ImportError as exc:
            raise LLMProviderError("requests library is required") from exc

        payload = {
            "model": self.model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query},
            ],
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(
                self.api_url, json=payload, headers=headers, timeout=timeout_seconds
            )
            response.raise_for_status()
            response_json = response.json()
        except requests.Timeout as exc:
            raise LLMProviderError(f"{self.get_name()} request timed out") from exc
        except requests.RequestException as exc:
            raise LLMProviderError(f"{self.get_name()} request failed: {str(exc)}") from exc
        except ValueError as exc:
            raise LLMProviderError(f"{self.get_name()} response is not valid JSON") from exc

        return self._extract_jetstream_response(response_json)

    def _extract_jetstream_response(self, response_json: dict[str, Any]) -> dict[str, Any]:
        choices = response_json.get("choices")
        if not isinstance(choices, list) or not choices:
            raise LLMProviderError(f"{self.get_name()} response has no choices")

        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            raise LLMProviderError(f"{self.get_name()} response choice format is invalid")

        message = first_choice.get("message", {})
        if not isinstance(message, dict):
            raise LLMProviderError(f"{self.get_name()} response message format is invalid")

        content = message.get("content", "")
        if not isinstance(content, str):
            raise LLMProviderError(f"{self.get_name()} response content is invalid")

        return {"content": content}


def get_providers_in_order() -> list[LLMProvider]:
    default_order = "groq,huggingface,jetstream"
    provider_order = os.getenv("INSIGHTOPS_LLM_PROVIDER_ORDER", default_order).strip() or default_order

    provider_names = [name.strip().lower() for name in provider_order.split(",")]

    provider_map = {
        "groq": GroqProvider(),
        "huggingface": HuggingFaceProvider(),
        "jetstream": JetstreamProvider(),
    }

    providers: list[LLMProvider] = []
    for name in provider_names:
        if name in provider_map:
            providers.append(provider_map[name])

    if not providers:
        providers = [GroqProvider(), HuggingFaceProvider(), JetstreamProvider()]

    return providers
