import json

import pytest

from code_tutor.config import ConfigManager, LLMRuntimeConfig
from code_tutor.llm_provider import (
    OpenAICompatibleLLMClient,
    create_llm_client,
    normalize_provider,
)


def _write_config(config_dir, data):
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "config.json").write_text(json.dumps(data), encoding="utf-8")


def test_provider_normalization_aliases():
    assert normalize_provider("anthropic") == "anthropic"
    assert normalize_provider("claude") == "anthropic"
    assert normalize_provider("openai") == "openai_compatible"
    assert normalize_provider("openai-compatible") == "openai_compatible"


def test_provider_normalization_rejects_unknown():
    with pytest.raises(ValueError):
        normalize_provider("unknown-provider")


def test_openai_provider_client_factory():
    client = create_llm_client(
        provider="openai_compatible",
        api_key="test-key",
        base_url="http://localhost:11434/v1",
    )
    assert isinstance(client, OpenAICompatibleLLMClient)


def test_openai_provider_prefers_openai_env(monkeypatch, tmp_path):
    config_dir = tmp_path / "config"
    _write_config(
        config_dir,
        {
            "provider": "openai_compatible",
            "api_key": "config-key",
        },
    )

    monkeypatch.delenv("CODE_TUTOR_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "openai-env-key")

    manager = ConfigManager(config_dir)
    manager.load()

    assert manager.get_api_key() == "openai-env-key"
    assert manager.is_api_key_from_env() is True


def test_openai_provider_does_not_use_anthropic_env(monkeypatch, tmp_path):
    config_dir = tmp_path / "config"
    _write_config(
        config_dir,
        {
            "provider": "openai_compatible",
            "api_key": "config-key",
        },
    )

    monkeypatch.delenv("CODE_TUTOR_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "anthropic-env-key")

    manager = ConfigManager(config_dir)
    manager.load()

    assert manager.get_api_key() == "config-key"


def test_openai_provider_base_url_default(tmp_path):
    config_dir = tmp_path / "config"
    _write_config(
        config_dir,
        {
            "provider": "openai_compatible",
            "api_key": "config-key",
            "model": "gpt-4o-mini",
        },
    )

    manager = ConfigManager(config_dir)
    manager.load()

    assert manager.get_base_url() == "https://api.openai.com/v1"


def test_anthropic_provider_base_url_is_none_by_default(tmp_path):
    config_dir = tmp_path / "config"
    _write_config(
        config_dir,
        {
            "provider": "anthropic",
            "api_key": "config-key",
        },
    )

    manager = ConfigManager(config_dir)
    manager.load()

    assert manager.get_base_url() is None


def test_openai_provider_default_model(tmp_path):
    config_dir = tmp_path / "config"
    _write_config(
        config_dir,
        {
            "provider": "openai_compatible",
            "api_key": "config-key",
            "model": "",
        },
    )

    manager = ConfigManager(config_dir)
    manager.load()

    assert manager.get_model() == "gpt-4o-mini"


def test_get_llm_runtime_returns_typed_settings(tmp_path):
    config_dir = tmp_path / "config"
    _write_config(
        config_dir,
        {
            "provider": "openai",
            "api_key": "config-key",
            "model": "gpt-4o-mini",
            "base_url": "https://example.com/v1",
        },
    )

    manager = ConfigManager(config_dir)
    runtime = manager.get_llm_runtime(reload_config=True)

    assert isinstance(runtime, LLMRuntimeConfig)
    assert runtime.provider == "openai_compatible"
    assert runtime.model == "gpt-4o-mini"
    assert runtime.base_url == "https://example.com/v1"


def test_invalid_loaded_config_is_normalized(tmp_path):
    config_dir = tmp_path / "config"
    _write_config(
        config_dir,
        {
            "provider": "not-a-provider",
            "model": 123,
            "base_url": 5,
            "experience_level": "guru",
            "preferences": "bad",
            "logging": "bad",
        },
    )

    manager = ConfigManager(config_dir)
    manager.load()

    assert manager.get_provider() == "anthropic"
    assert manager.get_model() == ConfigManager.DEFAULT_MODELS["anthropic"]
    assert manager.get_base_url() is None
    assert manager.get("experience_level") == "intermediate"
    assert manager.get("preferences.question_style") == "socratic"
    assert manager.is_logging_enabled() is False
    assert manager.has_unredacted_logging_consent() is False
