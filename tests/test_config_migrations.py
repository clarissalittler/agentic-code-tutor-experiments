import json

import pytest

from code_tutor.config import ConfigManager


def _write_config(config_dir, data):
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "config.json").write_text(
        json.dumps(data),
        encoding="utf-8",
    )


def test_legacy_config_without_version_is_migrated(tmp_path):
    config_dir = tmp_path / "config"
    _write_config(
        config_dir,
        {
            "api_key": "legacy-key",
            "logging": {
                "enabled": True,
                "redact_content": False,
            },
        },
    )

    manager = ConfigManager(config_dir)
    config = manager.load()

    assert config["config_version"] == ConfigManager.CURRENT_CONFIG_VERSION
    assert config["api_key"] == "legacy-key"
    assert config["logging"]["allow_unredacted"] is False


def test_invalid_config_version_is_treated_as_legacy_and_migrated(tmp_path):
    config_dir = tmp_path / "config"
    _write_config(
        config_dir,
        {
            "config_version": "not-a-number",
            "api_key": "legacy-key",
        },
    )

    manager = ConfigManager(config_dir)
    config = manager.load()

    assert config["config_version"] == ConfigManager.CURRENT_CONFIG_VERSION


def test_future_config_version_is_rejected(tmp_path):
    config_dir = tmp_path / "config"
    _write_config(
        config_dir,
        {
            "config_version": ConfigManager.CURRENT_CONFIG_VERSION + 1,
            "api_key": "new-key",
        },
    )

    manager = ConfigManager(config_dir)
    with pytest.raises(ValueError, match="newer than supported"):
        manager.load()


def test_save_writes_current_config_version(tmp_path):
    config_dir = tmp_path / "config"
    manager = ConfigManager(config_dir)

    manager.save({"api_key": "saved-key"})

    saved = json.loads((config_dir / "config.json").read_text(encoding="utf-8"))
    assert saved["config_version"] == ConfigManager.CURRENT_CONFIG_VERSION
