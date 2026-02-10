"""Shared CLI helpers for configuration and API logging."""

from pathlib import Path
from typing import Any, Dict, Optional

import click

from .config import ConfigManager
from .logger import SessionLogger
from .session_runtime import create_session_logger


def get_config_manager_from_context(ctx: click.Context) -> ConfigManager:
    """Create a config manager from Click context."""
    config_dir = ctx.obj.get("config_dir") if ctx.obj else None
    config_path = Path(config_dir) if config_dir else None
    return ConfigManager(config_path)


def load_config_or_raise(config_manager: ConfigManager) -> Dict[str, Any]:
    """Load config and raise a Click-friendly error if it fails."""
    try:
        return config_manager.load()
    except Exception as exc:
        raise click.ClickException(f"Error loading configuration: {exc}") from exc


def ensure_configured(config_manager: ConfigManager) -> Dict[str, Any]:
    """Load configuration and ensure API access is configured."""
    config = load_config_or_raise(config_manager)
    if not config_manager.is_configured():
        raise click.ClickException(
            "Code Tutor is not configured.\nRun 'code-tutor setup' first."
        )
    try:
        config_manager.assert_logging_safety()
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    return config


def start_api_logger(
    config_manager: ConfigManager,
    session_type: str,
    metadata: Dict[str, Any],
) -> Optional[SessionLogger]:
    """Start an API-call logger session when API logging is enabled."""
    if not (
        config_manager.is_logging_enabled() and config_manager.should_log_api_calls()
    ):
        return None

    try:
        logger = create_session_logger(config_manager)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    if logger is None:
        return None
    logger.start_session(session_type, metadata)
    return logger


def end_api_logger(logger: Optional[SessionLogger]) -> None:
    """End a started API logger session."""
    if logger:
        logger.end_session()
