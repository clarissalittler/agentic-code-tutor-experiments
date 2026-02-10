import json

import click
import pytest

from code_tutor.cli_support import (
    end_api_logger,
    ensure_configured,
    start_api_logger,
)
from code_tutor.config import ConfigManager


def _write_config(config_dir, config_data):
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "config.json").write_text(
        json.dumps(config_data),
        encoding="utf-8",
    )


def test_ensure_configured_returns_loaded_config(tmp_path):
    config_dir = tmp_path / "config"
    _write_config(config_dir, {"api_key": "test-key"})

    manager = ConfigManager(config_dir)
    config = ensure_configured(manager)

    assert config["api_key"] == "test-key"


def test_ensure_configured_raises_when_not_configured(tmp_path):
    config_dir = tmp_path / "config"
    _write_config(config_dir, {})

    manager = ConfigManager(config_dir)

    with pytest.raises(click.ClickException, match="Run 'code-tutor setup' first"):
        ensure_configured(manager)


def test_ensure_configured_blocks_unredacted_logging_without_consent(tmp_path):
    config_dir = tmp_path / "config"
    _write_config(
        config_dir,
        {
            "api_key": "test-key",
            "logging": {
                "enabled": True,
                "redact_content": False,
                "allow_unredacted": False,
            },
        },
    )

    manager = ConfigManager(config_dir)
    with pytest.raises(click.ClickException, match="Unredacted logging requires explicit consent"):
        ensure_configured(manager)


def test_ensure_configured_allows_unredacted_logging_with_consent(tmp_path):
    config_dir = tmp_path / "config"
    _write_config(
        config_dir,
        {
            "api_key": "test-key",
            "logging": {
                "enabled": True,
                "redact_content": False,
                "allow_unredacted": True,
            },
        },
    )

    manager = ConfigManager(config_dir)
    config = ensure_configured(manager)
    assert config["api_key"] == "test-key"


def test_start_api_logger_returns_none_when_api_logging_disabled(tmp_path):
    config_dir = tmp_path / "config"
    _write_config(
        config_dir,
        {
            "api_key": "test-key",
            "logging": {
                "enabled": True,
                "log_api_calls": False,
            },
        },
    )

    manager = ConfigManager(config_dir)
    manager.load()

    logger = start_api_logger(manager, "test", {"sample": True})
    assert logger is None


def test_start_api_logger_creates_session_when_enabled(tmp_path):
    config_dir = tmp_path / "config"
    _write_config(
        config_dir,
        {
            "api_key": "test-key",
            "logging": {
                "enabled": True,
                "log_api_calls": True,
                "redact_content": True,
            },
        },
    )

    manager = ConfigManager(config_dir)
    manager.load()

    logger = start_api_logger(manager, "test_session", {"sample": True})
    assert logger is not None
    assert logger.session_type == "test_session"

    end_api_logger(logger)
    assert logger.log_file.exists()
