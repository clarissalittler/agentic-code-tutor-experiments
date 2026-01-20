"""Configuration management for Code Tutor."""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


class ConfigManager:
    """Manages user configuration for Code Tutor.

    Configuration is loaded with the following precedence (highest to lowest):
    1. Environment variables (CODE_TUTOR_API_KEY or ANTHROPIC_API_KEY for API key)
    2. User config (~/.config/code-tutor/config.json)
    3. System config (/etc/code-tutor/config.json) - for shared server deployments
    4. Default values

    For classroom/shared server deployments:
    - Set API key via environment variable or system config with api_key_locked: true
    - Each student's preferences are stored in their own ~/.config/code-tutor/
    - Exercise directories are per-user by default (~/code-tutor-exercises/)
    """

    DEFAULT_CONFIG_DIR = Path.home() / ".config" / "code-tutor"
    SYSTEM_CONFIG_DIR = Path("/etc/code-tutor")
    CONFIG_FILE = "config.json"

    # Environment variables checked for API key (in order of precedence)
    API_KEY_ENV_VARS = ["CODE_TUTOR_API_KEY", "ANTHROPIC_API_KEY"]

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
    AVAILABLE_MODELS = [
        "claude-opus-4-5",
        "claude-sonnet-4-5",
        "claude-haiku-4-5",
    ]

    DEFAULT_CONFIG = {
        "api_key": "",
        "api_key_locked": False,
        "model": "claude-sonnet-4-5",
        "experience_level": "intermediate",
        "exercises_dir": "",  # Empty means use default ~/code-tutor-exercises/
        "preferences": {
            "question_style": "socratic",
            "verbosity": "medium",
            "focus_areas": ["design", "readability"],
        },
        "logging": {
            "enabled": False,
            "log_interactions": True,
            "log_api_calls": False,
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
        self._env_api_key: Optional[str] = None  # Cached env var API key

    def load(self) -> Dict[str, Any]:
        """Load configuration from file with precedence merging.

        Configuration is merged in this order (later overrides earlier):
        1. Default config
        2. System config (/etc/code-tutor/config.json) if exists
        3. User config (~/.config/code-tutor/config.json) if exists

        Environment variables for API key are checked separately in get_api_key().

        Returns:
            Configuration dictionary.
        """
        # Start with defaults
        self._config = self._deep_copy_config(self.DEFAULT_CONFIG)

        # Load and merge system config if exists (for shared server deployments)
        system_config_path = self.SYSTEM_CONFIG_DIR / self.CONFIG_FILE
        if system_config_path.exists():
            try:
                with open(system_config_path, "r") as f:
                    system_config = json.load(f)
                self._merge_config(self._config, system_config)
            except (json.JSONDecodeError, IOError):
                pass  # Silently ignore system config errors

        # Load and merge user config if exists
        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    user_config = json.load(f)
                self._merge_config(self._config, user_config)
            except (json.JSONDecodeError, IOError) as e:
                raise ValueError(f"Failed to load configuration: {e}")

        # Cache environment API key
        self._env_api_key = self._get_env_api_key()

        return self._config

    def _deep_copy_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a deep copy of a config dictionary.

        Args:
            config: Config to copy.

        Returns:
            Deep copy of the config.
        """
        result = {}
        for key, value in config.items():
            if isinstance(value, dict):
                result[key] = self._deep_copy_config(value)
            elif isinstance(value, list):
                result[key] = value.copy()
            else:
                result[key] = value
        return result

    def _merge_config(self, base: Dict[str, Any], override: Dict[str, Any]) -> None:
        """Merge override config into base config (modifies base in place).

        Args:
            base: Base config to merge into.
            override: Config values to merge.
        """
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value

    def _get_env_api_key(self) -> Optional[str]:
        """Get API key from environment variables.

        Returns:
            API key from environment or None.
        """
        for env_var in self.API_KEY_ENV_VARS:
            api_key = os.environ.get(env_var, "").strip()
            if api_key:
                return api_key
        return None

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

        Checks (in order): environment variable, config file.

        Returns:
            True if API key is set, False otherwise.
        """
        # Check environment variable first
        if self._env_api_key:
            return True
        # Then check config
        return bool(self.get("api_key"))

    def get_api_key(self) -> str:
        """Get the configured API key.

        Precedence: environment variable > config file.
        Environment variables checked: CODE_TUTOR_API_KEY, ANTHROPIC_API_KEY

        Returns:
            API key string.

        Raises:
            ValueError: If API key is not configured.
        """
        # Environment variable takes precedence
        if self._env_api_key:
            return self._env_api_key

        # Fall back to config file
        api_key = self.get("api_key", "")
        if not api_key:
            raise ValueError(
                "API key not configured. Either:\n"
                "  1. Run 'code-tutor setup' to configure\n"
                "  2. Set CODE_TUTOR_API_KEY or ANTHROPIC_API_KEY environment variable"
            )
        return api_key

    def get_exercises_dir(self) -> Path:
        """Get the exercises directory path.

        Returns:
            Path to exercises directory.
        """
        custom_dir = self.get("exercises_dir", "")
        if custom_dir:
            return Path(custom_dir).expanduser()
        return Path.home() / "code-tutor-exercises"

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

    def validate_model(self, model: str) -> bool:
        """Validate a model name.

        Args:
            model: Model name to validate.

        Returns:
            True if valid, False otherwise.
        """
        return model in self.AVAILABLE_MODELS

    def get_model(self) -> str:
        """Get the configured model.

        Returns:
            Model name string.
        """
        return self.get("model", "claude-sonnet-4-5")

    def is_logging_enabled(self) -> bool:
        """Check if logging is enabled.

        Returns:
            True if logging is enabled, False otherwise.
        """
        return self.get("logging.enabled", False)

    def should_log_interactions(self) -> bool:
        """Check if interaction logging is enabled.

        Returns:
            True if interaction logging is enabled, False otherwise.
        """
        return self.get("logging.log_interactions", True)

    def should_log_api_calls(self) -> bool:
        """Check if API call logging is enabled.

        Returns:
            True if API call logging is enabled, False otherwise.
        """
        return self.get("logging.log_api_calls", False)

    def is_api_key_locked(self) -> bool:
        """Check if the API key is locked from being changed.

        Returns:
            True if API key is locked, False otherwise.
        """
        return self.get("api_key_locked", False)

    def can_modify_api_key(self) -> bool:
        """Check if the API key can be modified.

        Returns:
            True if API key can be modified, False if it's locked.
        """
        return not self.is_api_key_locked()

    def is_api_key_from_env(self) -> bool:
        """Check if API key is being provided via environment variable.

        Returns:
            True if API key comes from environment, False otherwise.
        """
        return bool(self._env_api_key)

    def has_system_config(self) -> bool:
        """Check if a system-wide config exists.

        Returns:
            True if /etc/code-tutor/config.json exists, False otherwise.
        """
        return (self.SYSTEM_CONFIG_DIR / self.CONFIG_FILE).exists()
