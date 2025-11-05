"""Configuration management for Code Tutor."""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


class ConfigManager:
    """Manages user configuration for Code Tutor."""

    DEFAULT_CONFIG_DIR = Path.home() / ".config" / "code-tutor"
    CONFIG_FILE = "config.json"

    EXPERIENCE_LEVELS = ["beginner", "intermediate", "advanced", "expert"]
    QUESTION_STYLES = ["socratic", "direct", "exploratory"]
    FOCUS_AREAS = [
        "design",
        "readability",
        "performance",
        "security",
        "testing",
        "documentation",
    ]

    DEFAULT_CONFIG = {
        "api_key": "",
        "experience_level": "intermediate",
        "preferences": {
            "question_style": "socratic",
            "verbosity": "medium",
            "focus_areas": ["design", "readability"],
        },
    }

    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize the configuration manager.

        Args:
            config_dir: Optional custom configuration directory path.
        """
        self.config_dir = config_dir or self.DEFAULT_CONFIG_DIR
        self.config_path = self.config_dir / self.CONFIG_FILE
        self._config: Dict[str, Any] = {}

    def load(self) -> Dict[str, Any]:
        """Load configuration from file.

        Returns:
            Configuration dictionary.
        """
        if not self.config_path.exists():
            self._config = self.DEFAULT_CONFIG.copy()
            return self._config

        try:
            with open(self.config_path, "r") as f:
                self._config = json.load(f)
            return self._config
        except (json.JSONDecodeError, IOError) as e:
            raise ValueError(f"Failed to load configuration: {e}")

    def save(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Save configuration to file.

        Args:
            config: Optional configuration dictionary to save. If None, saves current config.
        """
        if config is not None:
            self._config = config

        # Ensure directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)

        try:
            with open(self.config_path, "w") as f:
                json.dump(self._config, f, indent=2)
        except IOError as e:
            raise ValueError(f"Failed to save configuration: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.

        Args:
            key: Configuration key (supports dot notation, e.g., 'preferences.verbosity').
            default: Default value if key not found.

        Returns:
            Configuration value or default.
        """
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        return value

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value.

        Args:
            key: Configuration key (supports dot notation).
            value: Value to set.
        """
        keys = key.split(".")
        config = self._config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def is_configured(self) -> bool:
        """Check if the tool is configured with an API key.

        Returns:
            True if API key is set, False otherwise.
        """
        return bool(self.get("api_key"))

    def get_api_key(self) -> str:
        """Get the configured API key.

        Returns:
            API key string.

        Raises:
            ValueError: If API key is not configured.
        """
        api_key = self.get("api_key", "")
        if not api_key:
            raise ValueError("API key not configured. Run 'code-tutor setup' first.")
        return api_key

    def validate_experience_level(self, level: str) -> bool:
        """Validate an experience level.

        Args:
            level: Experience level to validate.

        Returns:
            True if valid, False otherwise.
        """
        return level in self.EXPERIENCE_LEVELS

    def validate_question_style(self, style: str) -> bool:
        """Validate a question style.

        Args:
            style: Question style to validate.

        Returns:
            True if valid, False otherwise.
        """
        return style in self.QUESTION_STYLES

    def validate_focus_area(self, area: str) -> bool:
        """Validate a focus area.

        Args:
            area: Focus area to validate.

        Returns:
            True if valid, False otherwise.
        """
        return area in self.FOCUS_AREAS
