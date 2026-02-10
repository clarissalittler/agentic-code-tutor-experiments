import json
import pytest

from code_tutor.config import ConfigManager


def test_locked_api_key_ignores_env(monkeypatch, tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    config_path = config_dir / "config.json"
    config_path.write_text(
        json.dumps({"api_key": "config-key", "api_key_locked": True})
    )

    monkeypatch.setenv("CODE_TUTOR_API_KEY", "env-key")

    manager = ConfigManager(config_dir)
    manager.load()

    assert manager.get_api_key() == "config-key"
    assert manager.is_api_key_from_env() is False


def test_locked_api_key_requires_config(monkeypatch, tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    config_path = config_dir / "config.json"
    config_path.write_text(json.dumps({"api_key_locked": True}))

    monkeypatch.setenv("CODE_TUTOR_API_KEY", "env-key")

    manager = ConfigManager(config_dir)
    manager.load()

    with pytest.raises(ValueError):
        manager.get_api_key()


def test_unlocked_api_key_prefers_env(monkeypatch, tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    config_path = config_dir / "config.json"
    config_path.write_text(
        json.dumps({"api_key": "config-key", "api_key_locked": False})
    )

    monkeypatch.setenv("CODE_TUTOR_API_KEY", "env-key")

    manager = ConfigManager(config_dir)
    manager.load()

    assert manager.get_api_key() == "env-key"
