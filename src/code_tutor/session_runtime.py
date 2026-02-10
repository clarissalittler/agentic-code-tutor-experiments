"""Shared session runtime helpers for LLM/config/logging bootstrap."""

from dataclasses import dataclass
from typing import Any, Dict, Optional

from .config import ConfigManager, LLMRuntimeConfig
from .logger import SessionLogger

DEFAULT_PROOF_EXPERIENCE_LEVEL = "undergrad"
CODE_TO_PROOF_EXPERIENCE_LEVEL = {
    "beginner": "student",
    "intermediate": "undergrad",
    "advanced": "graduate",
    "expert": "researcher",
}


@dataclass(frozen=True)
class SessionRuntime:
    """Resolved runtime dependencies for an interactive session."""

    llm: LLMRuntimeConfig
    experience_level: str
    preferences: Dict[str, Any]
    logger: Optional[SessionLogger]
    log_api_calls: bool


def create_session_logger(config_manager: ConfigManager) -> Optional[SessionLogger]:
    """Create a configured session logger, enforcing logging safety policy."""
    if not config_manager.is_logging_enabled():
        return None

    config_manager.assert_logging_safety()
    return SessionLogger(
        config_dir=config_manager.config_dir,
        enabled=True,
        redact_content=config_manager.should_redact_logs(),
    )


def build_session_runtime(
    config_manager: ConfigManager,
    reload_config: bool = True,
) -> SessionRuntime:
    """Build a normalized runtime object for review/teaching/proof sessions."""
    llm = config_manager.get_llm_runtime(reload_config=reload_config)
    logger = create_session_logger(config_manager)
    log_api_calls = (
        config_manager.is_logging_enabled() and config_manager.should_log_api_calls()
    )

    return SessionRuntime(
        llm=llm,
        experience_level=config_manager.get("experience_level", "intermediate"),
        preferences=config_manager.get("preferences", {}),
        logger=logger,
        log_api_calls=log_api_calls,
    )


def map_code_to_proof_experience_level(code_experience_level: Optional[str]) -> str:
    """Map code-mode experience levels to proof-mode experience levels."""
    if not isinstance(code_experience_level, str):
        return DEFAULT_PROOF_EXPERIENCE_LEVEL
    return CODE_TO_PROOF_EXPERIENCE_LEVEL.get(
        code_experience_level,
        DEFAULT_PROOF_EXPERIENCE_LEVEL,
    )
