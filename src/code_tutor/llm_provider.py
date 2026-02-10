"""Provider-agnostic LLM client abstraction for Code Tutor."""

import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from urllib import error, request


ChatMessage = Dict[str, str]


@dataclass(frozen=True)
class LLMCompletion:
    """Provider completion payload with optional metadata."""

    text: str
    usage: Dict[str, Any]
    raw_response: Optional[Dict[str, Any]] = None


class LLMClient(ABC):
    """Abstract LLM chat client."""

    @abstractmethod
    def complete_with_metadata(
        self,
        model: str,
        messages: List[ChatMessage],
        max_tokens: int = 4096,
    ) -> LLMCompletion:
        """Generate a completion and metadata for chat-style messages."""

    def complete(
        self,
        model: str,
        messages: List[ChatMessage],
        max_tokens: int = 4096,
    ) -> str:
        """Compatibility helper returning only completion text."""
        return self.complete_with_metadata(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
        ).text


class AnthropicLLMClient(LLMClient):
    """Anthropic Messages API adapter."""

    def __init__(self, api_key: str):
        try:
            import anthropic
        except ImportError as exc:
            raise ValueError(
                "Anthropic provider requires the 'anthropic' package. "
                "Install dependencies or choose another provider."
            ) from exc

        self._client = anthropic.Anthropic(api_key=api_key)

    def complete_with_metadata(
        self,
        model: str,
        messages: List[ChatMessage],
        max_tokens: int = 4096,
    ) -> LLMCompletion:
        response = self._client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=messages,
        )
        return LLMCompletion(
            text=_extract_anthropic_text(response),
            usage=_extract_anthropic_usage(response),
        )


class OpenAICompatibleLLMClient(LLMClient):
    """OpenAI-compatible Chat Completions API adapter."""

    DEFAULT_BASE_URL = "https://api.openai.com/v1"
    RETRYABLE_STATUS_CODES = {408, 425, 429, 500, 502, 503, 504}

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        timeout_seconds: int = 120,
        max_retries: int = 2,
        retry_backoff_seconds: float = 1.0,
        max_backoff_seconds: float = 8.0,
    ):
        base = (base_url or self.DEFAULT_BASE_URL).rstrip("/")
        self._endpoint = f"{base}/chat/completions"
        self._api_key = api_key
        self._timeout_seconds = timeout_seconds
        self._max_retries = max(0, max_retries)
        self._retry_backoff_seconds = max(0.0, retry_backoff_seconds)
        self._max_backoff_seconds = max(self._retry_backoff_seconds, max_backoff_seconds)

    def complete_with_metadata(
        self,
        model: str,
        messages: List[ChatMessage],
        max_tokens: int = 4096,
    ) -> LLMCompletion:
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
        }
        body = json.dumps(payload).encode("utf-8")

        headers = {
            "Content-Type": "application/json",
        }
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        req = request.Request(
            self._endpoint,
            data=body,
            headers=headers,
            method="POST",
        )

        response_body: Optional[str] = None
        attempt = 0
        while attempt <= self._max_retries:
            try:
                with request.urlopen(req, timeout=self._timeout_seconds) as resp:
                    response_body = resp.read().decode("utf-8")
                break
            except error.HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="replace")
                should_retry = (
                    exc.code in self.RETRYABLE_STATUS_CODES
                    and attempt < self._max_retries
                )
                if should_retry:
                    retry_after = _parse_retry_after_seconds(exc.headers)
                    self._sleep_before_retry(attempt, retry_after)
                    attempt += 1
                    continue
                raise ValueError(
                    f"OpenAI-compatible API request failed ({exc.code}): {detail}"
                ) from exc
            except error.URLError as exc:
                if attempt < self._max_retries:
                    self._sleep_before_retry(attempt)
                    attempt += 1
                    continue
                raise ValueError(f"OpenAI-compatible API request failed: {exc}") from exc

        if response_body is None:
            raise ValueError("OpenAI-compatible API request failed with no response.")

        try:
            parsed = json.loads(response_body)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "OpenAI-compatible API returned invalid JSON."
            ) from exc

        choices = parsed.get("choices")
        if not choices:
            raise ValueError("OpenAI-compatible API response is missing choices.")

        choice = choices[0]
        content = ""
        if isinstance(choice, dict):
            message = choice.get("message")
            if isinstance(message, dict):
                content = _extract_openai_content(message.get("content", ""))
            elif isinstance(choice.get("text"), str):
                content = choice["text"]

        if not content and isinstance(parsed.get("output_text"), str):
            content = parsed["output_text"]

        if not content:
            raise ValueError(
                "OpenAI-compatible API response is missing assistant content."
            )

        usage = parsed.get("usage")
        if not isinstance(usage, dict):
            usage = {}

        return LLMCompletion(
            text=content,
            usage=usage,
            raw_response=parsed,
        )

    def _sleep_before_retry(
        self,
        attempt: int,
        retry_after_seconds: Optional[float] = None,
    ) -> None:
        """Sleep before a retry using Retry-After when available."""
        if retry_after_seconds is not None and retry_after_seconds >= 0:
            time.sleep(min(retry_after_seconds, self._max_backoff_seconds))
            return

        delay = self._retry_backoff_seconds * (2 ** attempt)
        time.sleep(min(delay, self._max_backoff_seconds))


def normalize_provider(provider: Optional[str]) -> str:
    """Normalize provider aliases to canonical values."""
    value = (provider or "anthropic").strip().lower().replace("-", "_")
    aliases = {
        "anthropic": "anthropic",
        "claude": "anthropic",
        "openai": "openai_compatible",
        "openai_compatible": "openai_compatible",
        "openai_compat": "openai_compatible",
    }
    if value in aliases:
        return aliases[value]

    raise ValueError(
        f"Unknown provider '{provider}'. "
        "Supported providers: anthropic, openai_compatible"
    )


def create_llm_client(
    provider: Optional[str],
    api_key: str,
    base_url: Optional[str] = None,
) -> LLMClient:
    """Create a provider-specific LLM client."""
    normalized = normalize_provider(provider)

    if normalized == "anthropic":
        return AnthropicLLMClient(api_key=api_key)
    if normalized == "openai_compatible":
        return OpenAICompatibleLLMClient(api_key=api_key, base_url=base_url)

    # Defensive fallback for future branch changes.
    raise ValueError(f"Unsupported provider: {normalized}")


def _extract_anthropic_text(response: Any) -> str:
    """Extract plain text from an Anthropic message response."""
    content = getattr(response, "content", None)
    if not content:
        return ""

    text_chunks: List[str] = []
    for block in content:
        block_text = getattr(block, "text", None)
        if isinstance(block_text, str) and block_text:
            text_chunks.append(block_text)

    if text_chunks:
        return "\n".join(text_chunks)
    return str(content)


def _extract_anthropic_usage(response: Any) -> Dict[str, Any]:
    """Extract token usage details from an Anthropic response object."""
    usage = getattr(response, "usage", None)
    if usage is None:
        return {}

    usage_data: Dict[str, Any] = {}
    for field in (
        "input_tokens",
        "output_tokens",
        "cache_creation_input_tokens",
        "cache_read_input_tokens",
    ):
        value = getattr(usage, field, None)
        if isinstance(value, int):
            usage_data[field] = value

    if "input_tokens" in usage_data and "output_tokens" in usage_data:
        usage_data["total_tokens"] = (
            usage_data["input_tokens"] + usage_data["output_tokens"]
        )

    return usage_data


def _parse_retry_after_seconds(headers: Any) -> Optional[float]:
    """Parse Retry-After header value into seconds."""
    if headers is None:
        return None

    retry_after = headers.get("Retry-After")
    if retry_after is None:
        return None

    try:
        value = float(str(retry_after).strip())
    except ValueError:
        return None

    if value < 0:
        return None
    return value


def _extract_openai_content(content: Any) -> str:
    """Extract text from OpenAI-compatible content payloads."""
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts: List[str] = []
        for item in content:
            if not isinstance(item, dict):
                continue

            if item.get("type") == "text":
                text = item.get("text", "")
                if isinstance(text, str) and text:
                    parts.append(text)
                continue

            text = item.get("text")
            if isinstance(text, str) and text:
                parts.append(text)

        return "\n".join(parts)

    return str(content)
