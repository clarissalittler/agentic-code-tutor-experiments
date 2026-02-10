"""Configuration management for Code Tutor."""

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from .llm_provider import normalize_provider


@dataclass(frozen=True)
class LLMRuntimeConfig:
    """Typed runtime settings required to call an LLM provider."""

    api_key: str
    model: str
    provider: str
    base_url: Optional[str]


class ConfigManager:
    """Manages user configuration for Code Tutor.

    Configuration is loaded with the following precedence (highest to lowest):
    1. Environment variables (provider-specific API key env vars)
    2. User config (~/.config/code-tutor/config.json)
    3. System config (/etc/code-tutor/config.json) - for shared server deployments
    4. Default values

    For classroom/shared server deployments:
    - Set API key in system config with api_key_locked: true (environment variables are ignored)
    - Each student's preferences are stored in their own ~/.config/code-tutor/
    - Exercise directories are per-user by default (~/code-tutor-exercises/)
    """

    DEFAULT_CONFIG_DIR = Path.home() / ".config" / "code-tutor"
    SYSTEM_CONFIG_DIR = Path("/etc/code-tutor")
    CONFIG_FILE = "config.json"
    CONFIG_VERSION_KEY = "config_version"
    CURRENT_CONFIG_VERSION = 2

    # Default environment variables checked for API key (in order of precedence)
    API_KEY_ENV_VARS = ["CODE_TUTOR_API_KEY", "ANTHROPIC_API_KEY"]
    PROVIDER_API_KEY_ENV_VARS = {
        "anthropic": ["CODE_TUTOR_API_KEY", "ANTHROPIC_API_KEY"],
        "openai_compatible": ["CODE_TUTOR_API_KEY", "OPENAI_API_KEY"],
    }

    AVAILABLE_PROVIDERS = ["anthropic", "openai_compatible"]
    DEFAULT_MODELS = {
        "anthropic": "claude-sonnet-4-5",
        "openai_compatible": "gpt-4o-mini",
    }

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
        "config_version": CURRENT_CONFIG_VERSION,
        "provider": "anthropic",
        "api_key": "",
        "api_key_locked": False,
        "model": "claude-sonnet-4-5",
        "base_url": "",
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
            "redact_content": True,
            "allow_unredacted": False,
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

        Environment variables for API key are checked separately in get_api_key(),
        unless the API key is locked.

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
                system_config = self._migrate_config(system_config, source="system")
                self._merge_config(self._config, system_config)
            except (json.JSONDecodeError, IOError, ValueError):
                pass  # Silently ignore system config errors

        # Load and merge user config if exists
        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    user_config = json.load(f)
                user_config = self._migrate_config(user_config, source="user")
                self._merge_config(self._config, user_config)
            except (json.JSONDecodeError, IOError) as e:
                raise ValueError(f"Failed to load configuration: {e}")
            except ValueError as e:
                raise ValueError(f"Failed to load configuration: {e}")

        # Cache environment API key based on configured provider
        self._normalize_loaded_config()
        self._env_api_key = self._get_env_api_key(self.get("provider", "anthropic"))

        return self._config

    def _migrate_config(self, config: Any, source: str) -> Dict[str, Any]:
        """Migrate a loaded config dictionary to current version."""
        if not isinstance(config, dict):
            raise ValueError(f"{source} config must be a JSON object.")

        migrated = self._deep_copy_config(config)
        version = self._read_config_version(migrated)

        if version > self.CURRENT_CONFIG_VERSION:
            raise ValueError(
                f"{source} config version {version} is newer than supported "
                f"version {self.CURRENT_CONFIG_VERSION}. Please upgrade Code Tutor."
            )

        while version < self.CURRENT_CONFIG_VERSION:
            if version == 1:
                migrated = self._migrate_v1_to_v2(migrated)
            else:
                raise ValueError(
                    f"{source} config version {version} cannot be migrated "
                    f"to version {self.CURRENT_CONFIG_VERSION}."
                )

            next_version = self._read_config_version(migrated)
            if next_version <= version:
                raise ValueError(
                    f"{source} config migration failed to advance version "
                    f"(stuck at {version})."
                )
            version = next_version

        migrated[self.CONFIG_VERSION_KEY] = self.CURRENT_CONFIG_VERSION
        return migrated

    def _read_config_version(self, config: Dict[str, Any]) -> int:
        """Read config version, treating missing/invalid as legacy v1."""
        raw_version = config.get(self.CONFIG_VERSION_KEY)
        if raw_version is None:
            return 1

        if isinstance(raw_version, bool):
            return 1

        if isinstance(raw_version, int):
            return raw_version if raw_version >= 1 else 1

        if isinstance(raw_version, str):
            stripped = raw_version.strip()
            if not stripped:
                return 1
            try:
                parsed = int(stripped)
            except ValueError:
                return 1
            return parsed if parsed >= 1 else 1

        return 1

    def _migrate_v1_to_v2(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate legacy config schema to v2."""
        logging_config = config.get("logging")
        if not isinstance(logging_config, dict):
            logging_config = {}
        logging_config.setdefault("allow_unredacted", False)
        config["logging"] = logging_config
        config[self.CONFIG_VERSION_KEY] = 2
        return config

    def _normalize_loaded_config(self) -> None:
        """Normalize and validate loaded config values."""
        self._config[self.CONFIG_VERSION_KEY] = self.CURRENT_CONFIG_VERSION

        # Provider normalization
        provider_value = self._config.get("provider", self.DEFAULT_CONFIG["provider"])
        try:
            provider = normalize_provider(provider_value)
        except ValueError:
            provider = self.DEFAULT_CONFIG["provider"]
        self._config["provider"] = provider

        # Top-level scalar values
        api_key = self._config.get("api_key", "")
        self._config["api_key"] = api_key.strip() if isinstance(api_key, str) else ""

        self._config["api_key_locked"] = bool(
            self._config.get(
                "api_key_locked",
                self.DEFAULT_CONFIG["api_key_locked"],
            )
        )

        model = self._config.get("model", "")
        if not isinstance(model, str):
            model = ""
        model = model.strip()
        self._config["model"] = model or self.DEFAULT_MODELS.get(
            provider, self.DEFAULT_MODELS["anthropic"]
        )

        base_url = self._config.get("base_url", "")
        self._config["base_url"] = base_url.strip() if isinstance(base_url, str) else ""

        experience_level = self._config.get(
            "experience_level",
            self.DEFAULT_CONFIG["experience_level"],
        )
        if experience_level not in self.EXPERIENCE_LEVELS:
            experience_level = self.DEFAULT_CONFIG["experience_level"]
        self._config["experience_level"] = experience_level

        exercises_dir = self._config.get("exercises_dir", "")
        self._config["exercises_dir"] = (
            exercises_dir.strip() if isinstance(exercises_dir, str) else ""
        )

        # Preferences shape and values
        default_preferences = self.DEFAULT_CONFIG["preferences"]
        preferences = self._config.get("preferences")
        if not isinstance(preferences, dict):
            preferences = self._deep_copy_config(default_preferences)
        else:
            question_style = preferences.get(
                "question_style", default_preferences["question_style"]
            )
            if question_style not in self.QUESTION_STYLES:
                question_style = default_preferences["question_style"]

            verbosity = preferences.get("verbosity", default_preferences["verbosity"])
            if not isinstance(verbosity, str) or not verbosity.strip():
                verbosity = default_preferences["verbosity"]

            focus_areas = preferences.get(
                "focus_areas",
                default_preferences["focus_areas"],
            )
            if not isinstance(focus_areas, list):
                focus_areas = []
            focus_areas = [
                area for area in focus_areas
                if isinstance(area, str) and area in self.FOCUS_AREAS
            ]
            if not focus_areas:
                focus_areas = list(default_preferences["focus_areas"])

            preferences = {
                "question_style": question_style,
                "verbosity": verbosity.strip(),
                "focus_areas": focus_areas,
            }
        self._config["preferences"] = preferences

        # Logging shape and values
        default_logging = self.DEFAULT_CONFIG["logging"]
        logging_config = self._config.get("logging")
        if not isinstance(logging_config, dict):
            logging_config = self._deep_copy_config(default_logging)
        else:
            logging_config = {
                "enabled": bool(logging_config.get("enabled", default_logging["enabled"])),
                "log_interactions": bool(
                    logging_config.get(
                        "log_interactions",
                        default_logging["log_interactions"],
                    )
                ),
                "log_api_calls": bool(
                    logging_config.get("log_api_calls", default_logging["log_api_calls"])
                ),
                "redact_content": bool(
                    logging_config.get(
                        "redact_content",
                        default_logging["redact_content"],
                    )
                ),
                "allow_unredacted": bool(
                    logging_config.get(
                        "allow_unredacted",
                        default_logging["allow_unredacted"],
                    )
                ),
            }
        self._config["logging"] = logging_config

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

    def _get_env_api_key(self, provider: Optional[str] = None) -> Optional[str]:
        """Get API key from environment variables.

        Returns:
            API key from environment or None.
        """
        for env_var in self._env_vars_for_provider(provider):
            api_key = os.environ.get(env_var, "").strip()
            if api_key:
                return api_key
        return None

    def _env_vars_for_provider(self, provider: Optional[str]) -> List[str]:
        """Get API key environment variables for a provider."""
        try:
            normalized = normalize_provider(provider)
            return self.PROVIDER_API_KEY_ENV_VARS.get(
                normalized, self.API_KEY_ENV_VARS
            )
        except ValueError:
            return self.API_KEY_ENV_VARS

    def save(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Save configuration to file.

        Args:
            config: Optional configuration dictionary to save. If None, saves current config.
        """
        if config is not None:
            self._config = config
        self._config[self.CONFIG_VERSION_KEY] = self.CURRENT_CONFIG_VERSION

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
        if self.is_api_key_locked():
            return bool(self.get("api_key"))
        self._env_api_key = self._get_env_api_key(self.get("provider", "anthropic"))
        # Check environment variable first
        if self._env_api_key:
            return True
        # Then check config
        return bool(self.get("api_key"))

    def get_api_key(self) -> str:
        """Get the configured API key.

        Precedence: environment variable > config file (unless API key is locked).

        Returns:
            API key string.

        Raises:
            ValueError: If API key is not configured.
        """
        if self.is_api_key_locked():
            api_key = self.get("api_key", "")
            if not api_key:
                raise ValueError(
                    "API key is locked but not configured. "
                    "Please contact your administrator."
                )
            return api_key

        # Environment variable takes precedence
        self._env_api_key = self._get_env_api_key(self.get("provider", "anthropic"))
        if self._env_api_key:
            return self._env_api_key

        # Fall back to config file
        api_key = self.get("api_key", "")
        if not api_key:
            env_vars = ", ".join(
                self._env_vars_for_provider(self.get("provider", "anthropic"))
            )
            raise ValueError(
                "API key not configured. Either:\n"
                "  1. Run 'code-tutor setup' to configure\n"
                f"  2. Set one of these environment variables: {env_vars}"
            )
        return api_key

    def get_llm_runtime(self, reload_config: bool = False) -> LLMRuntimeConfig:
        """Return typed runtime LLM settings.

        Args:
            reload_config: Whether to reload configuration from disk first.

        Returns:
            LLMRuntimeConfig with resolved provider settings.
        """
        if reload_config or not self._config:
            self.load()

        return LLMRuntimeConfig(
            api_key=self.get_api_key(),
            model=self.get_model(),
            provider=self.get_provider(),
            base_url=self.get_base_url(),
        )

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
        provider = self.get_provider()
        if provider == "anthropic":
            return model in self.AVAILABLE_MODELS
        return bool(model and model.strip())

    def validate_provider(self, provider: str) -> bool:
        """Validate a provider name."""
        try:
            normalize_provider(provider)
            return True
        except ValueError:
            return False

    def get_model(self) -> str:
        """Get the configured model.

        Returns:
            Model name string.
        """
        configured = self.get("model", "")
        if configured:
            return configured
        provider = self.get_provider()
        return self.DEFAULT_MODELS.get(provider, self.DEFAULT_MODELS["anthropic"])

    def get_provider(self) -> str:
        """Get the configured LLM provider."""
        provider = self.get("provider", "anthropic")
        return normalize_provider(provider)

    def get_base_url(self) -> Optional[str]:
        """Get optional API base URL for provider backends."""
        base_url = self.get("base_url", "")
        if base_url:
            return str(base_url).strip()
        if self.get_provider() == "openai_compatible":
            return "https://api.openai.com/v1"
        return None

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

    def should_redact_logs(self) -> bool:
        """Check if log content should be redacted.

        Returns:
            True if log content should be redacted, False otherwise.
        """
        return self.get("logging.redact_content", True)

    def has_unredacted_logging_consent(self) -> bool:
        """Check if user explicitly consented to unredacted log content."""
        return self.get("logging.allow_unredacted", False)

    def requires_unredacted_logging_consent(self) -> bool:
        """Check whether unredacted logging is enabled without consent."""
        return (
            self.is_logging_enabled()
            and not self.should_redact_logs()
            and not self.has_unredacted_logging_consent()
        )

    def assert_logging_safety(self) -> None:
        """Raise when configured logging would write unredacted content unsafely."""
        if self.requires_unredacted_logging_consent():
            raise ValueError(
                "Unredacted logging requires explicit consent. "
                "Run 'code-tutor setup' and confirm unredacted logging, "
                "or enable redacted logs."
            )

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
        self._env_api_key = self._get_env_api_key(self.get("provider", "anthropic"))
        return bool(self._env_api_key) and not self.is_api_key_locked()

    def has_system_config(self) -> bool:
        """Check if a system-wide config exists.

        Returns:
            True if /etc/code-tutor/config.json exists, False otherwise.
        """
        return (self.SYSTEM_CONFIG_DIR / self.CONFIG_FILE).exists()
