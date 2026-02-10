import io
import json
from urllib import error

import pytest

from code_tutor.llm_provider import (
    OpenAICompatibleLLMClient,
    _extract_anthropic_usage,
)


class _FakeResponse:
    def __init__(self, payload):
        self._body = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return self._body


def test_openai_client_retries_on_rate_limit_then_succeeds(monkeypatch):
    attempts = {"count": 0}
    sleeps = []

    def fake_urlopen(req, timeout):
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise error.HTTPError(
                req.full_url,
                429,
                "Too Many Requests",
                {"Retry-After": "0"},
                io.BytesIO(b'{"error":"rate_limit"}'),
            )
        return _FakeResponse(
            {
                "choices": [{"message": {"content": "retry success"}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 3},
            }
        )

    monkeypatch.setattr("code_tutor.llm_provider.request.urlopen", fake_urlopen)
    monkeypatch.setattr("code_tutor.llm_provider.time.sleep", lambda seconds: sleeps.append(seconds))

    client = OpenAICompatibleLLMClient(
        api_key="test-key",
        base_url="https://example.com/v1",
        max_retries=2,
    )
    completion = client.complete_with_metadata(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "hello"}],
    )

    assert completion.text == "retry success"
    assert completion.usage["prompt_tokens"] == 10
    assert completion.usage["completion_tokens"] == 3
    assert attempts["count"] == 2
    assert sleeps == [0.0]


def test_openai_client_retries_on_url_error(monkeypatch):
    attempts = {"count": 0}
    sleeps = []

    def fake_urlopen(req, timeout):
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise error.URLError("temporary network failure")
        return _FakeResponse({"choices": [{"message": {"content": "ok"}}], "usage": {}})

    monkeypatch.setattr("code_tutor.llm_provider.request.urlopen", fake_urlopen)
    monkeypatch.setattr("code_tutor.llm_provider.time.sleep", lambda seconds: sleeps.append(seconds))

    client = OpenAICompatibleLLMClient(
        api_key="test-key",
        base_url="https://example.com/v1",
        max_retries=2,
        retry_backoff_seconds=0.25,
        max_backoff_seconds=1.0,
    )
    completion = client.complete_with_metadata(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "hello"}],
    )

    assert completion.text == "ok"
    assert attempts["count"] == 2
    assert sleeps == [0.25]


def test_openai_client_raises_on_non_retryable_http_error(monkeypatch):
    def fake_urlopen(req, timeout):
        raise error.HTTPError(
            req.full_url,
            400,
            "Bad Request",
            {},
            io.BytesIO(b'{"error":"bad_request"}'),
        )

    monkeypatch.setattr("code_tutor.llm_provider.request.urlopen", fake_urlopen)
    monkeypatch.setattr("code_tutor.llm_provider.time.sleep", lambda seconds: None)

    client = OpenAICompatibleLLMClient(
        api_key="test-key",
        base_url="https://example.com/v1",
        max_retries=2,
    )

    with pytest.raises(ValueError, match="400"):
        client.complete_with_metadata(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "hello"}],
        )


class _AnthropicUsageFixture:
    def __init__(
        self,
        input_tokens=None,
        output_tokens=None,
        cache_creation_input_tokens=None,
        cache_read_input_tokens=None,
    ):
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.cache_creation_input_tokens = cache_creation_input_tokens
        self.cache_read_input_tokens = cache_read_input_tokens


class _AnthropicResponseFixture:
    def __init__(self, usage):
        self.usage = usage


def test_extract_anthropic_usage_contract_full_fields():
    response = _AnthropicResponseFixture(
        _AnthropicUsageFixture(
            input_tokens=120,
            output_tokens=45,
            cache_creation_input_tokens=10,
            cache_read_input_tokens=20,
        )
    )

    usage = _extract_anthropic_usage(response)
    assert usage == {
        "input_tokens": 120,
        "output_tokens": 45,
        "cache_creation_input_tokens": 10,
        "cache_read_input_tokens": 20,
        "total_tokens": 165,
    }


def test_extract_anthropic_usage_contract_missing_fields():
    response = _AnthropicResponseFixture(
        _AnthropicUsageFixture(
            input_tokens=33,
            output_tokens=None,
            cache_creation_input_tokens="not-an-int",
        )
    )

    usage = _extract_anthropic_usage(response)
    assert usage == {"input_tokens": 33}


def test_extract_anthropic_usage_contract_no_usage_object():
    response = _AnthropicResponseFixture(None)
    assert _extract_anthropic_usage(response) == {}
