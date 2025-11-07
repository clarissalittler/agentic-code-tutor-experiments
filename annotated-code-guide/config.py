"""
Configuration management for Code Tutor.

📚 FILE OVERVIEW:
This file implements a configuration manager that handles loading, saving, and
accessing user preferences for the Code Tutor application. It's a great example
of the Configuration Manager pattern.

🎯 WHAT YOU'LL LEARN:
- JSON-based configuration storage
- Dot-notation access to nested dictionaries
- Configuration validation patterns
- Using pathlib for cross-platform file paths
- Type hints for better code documentation
- Class-level constants for configuration options

💡 WHY THIS FILE EXISTS:
Every CLI application needs to remember user preferences between runs. This file
provides a clean, centralized way to manage those preferences with validation
and default values.
"""

# ============================================================================
# IMPORTS
# ============================================================================

import json  # 🔍 JSON for human-readable config files (easy to edit manually)
import os   # Not actually used in this file - could be removed
from pathlib import Path  # 🎯 Modern Python way to handle file paths (cross-platform)
from typing import Any, Dict, Optional  # 💡 Type hints make code self-documenting


# ============================================================================
# ConfigManager CLASS
# ============================================================================

class ConfigManager:
    """
    Manages user configuration for Code Tutor.

    🔍 DESIGN PATTERN: Configuration Manager
    This class follows the Configuration Manager pattern, providing:
    - Single source of truth for configuration
    - Centralized validation
    - Easy access with dot notation
    - Automatic directory/file creation

    💡 KEY FEATURES:
    - Stores config in ~/.config/code-tutor/config.json (follows Linux conventions)
    - Supports nested config access like "preferences.verbosity"
    - Validates values against predefined constants
    - Provides sensible defaults
    """

    # ------------------------------------------------------------------------
    # CLASS CONSTANTS
    # ------------------------------------------------------------------------
    # 🎯 These define WHERE config is stored and WHAT values are allowed

    # Default location: ~/.config/code-tutor/
    # 🔍 Path.home() is cross-platform (works on Windows, Mac, Linux)
    DEFAULT_CONFIG_DIR = Path.home() / ".config" / "code-tutor"
    CONFIG_FILE = "config.json"

    # 💡 Valid options are stored as class constants - this makes them easy to reference
    # and ensures consistency across the application

    EXPERIENCE_LEVELS = ["beginner", "intermediate", "advanced", "expert"]
    # 🎯 Different question styles for different learning preferences
    QUESTION_STYLES = ["socratic", "direct", "exploratory"]

    # Areas of focus for code review
    FOCUS_AREAS = [
        "design",         # Architecture and design patterns
        "readability",    # Code clarity and maintainability
        "performance",    # Speed and efficiency
        "security",       # Vulnerabilities and best practices
        "testing",        # Test coverage and quality
        "documentation",  # Comments and docstrings
    ]

    # Available Claude models
    # ⚠️ These must match the actual model names in Anthropic's API
    AVAILABLE_MODELS = [
        "claude-sonnet-4-5",  # Balanced performance
        "claude-haiku-4-5",   # Fast and cost-effective
    ]

    # 🔍 DEFAULT CONFIG: Sensible defaults for first-time users
    DEFAULT_CONFIG = {
        "api_key": "",  # Empty - user must set this
        "model": "claude-sonnet-4-5",  # Sonnet is the default (balanced)
        "experience_level": "intermediate",  # Most common level
        "preferences": {
            "question_style": "socratic",  # Socratic method is most educational
            "verbosity": "medium",  # Not too verbose, not too terse
            "focus_areas": ["design", "readability"],  # Most common concerns
        },
        "logging": {
            "enabled": False,  # 🎯 Disabled by default (privacy)
            "log_interactions": True,  # What to log (if enabled)
            "log_api_calls": False,  # API calls can be verbose
        },
    }

    # ------------------------------------------------------------------------
    # INITIALIZATION
    # ------------------------------------------------------------------------

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize the configuration manager.

        🔍 PATTERN: Dependency Injection
        By accepting config_dir as a parameter, we make testing easier.
        Tests can pass a temporary directory instead of using ~/.config

        Args:
            config_dir: Optional custom configuration directory path.
                       If None, uses DEFAULT_CONFIG_DIR (~/.config/code-tutor)
        """
        # Use provided directory or fall back to default
        # 💡 This is the "or" pattern: if config_dir is None, use DEFAULT_CONFIG_DIR
        self.config_dir = config_dir or self.DEFAULT_CONFIG_DIR

        # Build the full path to the config file
        # 🎯 Using Path's / operator is cleaner than os.path.join()
        self.config_path = self.config_dir / self.CONFIG_FILE

        # Internal storage for the loaded configuration
        # 🔍 Type hint says this is a dictionary with string keys and any values
        self._config: Dict[str, Any] = {}

    # ------------------------------------------------------------------------
    # LOADING AND SAVING
    # ------------------------------------------------------------------------

    def load(self) -> Dict[str, Any]:
        """
        Load configuration from file.

        🔍 KEY CONCEPT: File I/O with error handling
        This method demonstrates:
        1. Checking if file exists before reading
        2. Using 'with' for automatic file closing
        3. Handling JSON parsing errors
        4. Returning defaults if file doesn't exist

        Returns:
            Configuration dictionary.
        """
        # Check if config file exists
        # 🎯 pathlib's exists() is cleaner than os.path.exists()
        if not self.config_path.exists():
            # If no config file, return defaults
            # ⚠️ Use .copy() to avoid modifying the class constant
            self._config = self.DEFAULT_CONFIG.copy()
            return self._config

        try:
            # 🔍 'with' statement ensures file is closed even if error occurs
            with open(self.config_path, "r") as f:
                # Parse JSON file into Python dictionary
                self._config = json.load(f)
            return self._config

        except (json.JSONDecodeError, IOError) as e:
            # 🎯 Catch specific exceptions:
            # - JSONDecodeError: Invalid JSON syntax
            # - IOError: Can't read file (permissions, etc.)
            raise ValueError(f"Failed to load configuration: {e}")

    def save(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Save configuration to file.

        🔍 KEY CONCEPT: Creating directories and writing JSON
        This method:
        1. Creates the config directory if it doesn't exist
        2. Writes the config as formatted JSON (indent=2 for readability)
        3. Handles write errors gracefully

        Args:
            config: Optional configuration dictionary to save.
                   If None, saves current config (self._config).
        """
        # If config provided, update internal state
        if config is not None:
            self._config = config

        # Create directory if it doesn't exist
        # 🎯 parents=True creates parent directories too (like 'mkdir -p')
        # 🎯 exist_ok=True means no error if directory already exists
        self.config_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Write JSON file with nice formatting
            # 💡 indent=2 makes the JSON human-readable
            with open(self.config_path, "w") as f:
                json.dump(self._config, f, indent=2)

        except IOError as e:
            # ⚠️ Common causes: Permission denied, disk full, read-only filesystem
            raise ValueError(f"Failed to save configuration: {e}")

    # ------------------------------------------------------------------------
    # ACCESSING CONFIGURATION
    # ------------------------------------------------------------------------

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value with dot notation support.

        🔍 KEY CONCEPT: Dot notation for nested dictionaries
        Instead of: config["preferences"]["verbosity"]
        We can use: config.get("preferences.verbosity")

        This makes code more readable and is common in modern config libraries.

        💡 HOW IT WORKS:
        1. Split key by dots: "preferences.verbosity" → ["preferences", "verbosity"]
        2. Navigate through nested dicts one level at a time
        3. Return default if any level doesn't exist

        Args:
            key: Configuration key (supports dot notation, e.g., 'preferences.verbosity').
            default: Default value if key not found.

        Returns:
            Configuration value or default.

        Example:
            >>> config.get("model")  # Returns "claude-sonnet-4-5"
            >>> config.get("preferences.question_style")  # Returns "socratic"
            >>> config.get("nonexistent", "default")  # Returns "default"
        """
        # Split the key into parts
        # 🔍 "preferences.verbosity".split(".") → ["preferences", "verbosity"]
        keys = key.split(".")

        # Start at the root of the config
        value = self._config

        # Navigate through each level
        for k in keys:
            # Check if current value is a dictionary (can we go deeper?)
            if isinstance(value, dict):
                # Get the next level
                value = value.get(k)

                # If None, key doesn't exist at this level
                if value is None:
                    return default
            else:
                # We tried to access a key on a non-dict (e.g., trying to access
                # "model.something" when "model" is a string)
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value with dot notation support.

        🔍 KEY CONCEPT: Creating nested dictionaries on-the-fly
        This method creates intermediate dictionaries if they don't exist.

        💡 HOW IT WORKS:
        For "preferences.verbosity" = "high":
        1. Split into ["preferences", "verbosity"]
        2. Navigate to "preferences" (create if doesn't exist)
        3. Set "verbosity" = "high" in that dictionary

        Args:
            key: Configuration key (supports dot notation).
            value: Value to set.

        Example:
            >>> config.set("model", "claude-haiku-4-5")
            >>> config.set("preferences.verbosity", "high")
            >>> config.set("new.nested.key", "value")  # Creates nested dicts
        """
        # Split key into parts
        keys = key.split(".")

        # Start at root
        config = self._config

        # Navigate to the parent of the final key
        # 🔍 keys[:-1] means "all except the last"
        # For "preferences.verbosity", this loops once for "preferences"
        for k in keys[:-1]:
            # If this key doesn't exist, create an empty dict
            if k not in config:
                config[k] = {}
            # Move deeper into the nested structure
            config = config[k]

        # Set the final key
        # 🔍 keys[-1] is the last element
        # For "preferences.verbosity", this sets config["verbosity"] = value
        config[keys[-1]] = value

    # ------------------------------------------------------------------------
    # CONVENIENCE METHODS
    # ------------------------------------------------------------------------
    # 💡 These methods provide clean, semantic access to common operations

    def is_configured(self) -> bool:
        """
        Check if the tool is configured with an API key.

        🎯 This is used to check if the user has completed setup.

        Returns:
            True if API key is set, False otherwise.
        """
        # bool("") is False, bool("any-string") is True
        # 🔍 This checks if api_key exists and is non-empty
        return bool(self.get("api_key"))

    def get_api_key(self) -> str:
        """
        Get the configured API key.

        ⚠️ This method RAISES an error if key is not configured.
        This is intentional - we want to fail fast if key is missing.

        Returns:
            API key string.

        Raises:
            ValueError: If API key is not configured.
        """
        api_key = self.get("api_key", "")

        # If empty, raise a helpful error message
        if not api_key:
            raise ValueError("API key not configured. Run 'code-tutor setup' first.")

        return api_key

    # ------------------------------------------------------------------------
    # VALIDATION METHODS
    # ------------------------------------------------------------------------
    # 💡 These ensure user inputs match allowed values

    def validate_experience_level(self, level: str) -> bool:
        """
        Validate an experience level.

        🔍 PATTERN: Validation against constants
        By storing valid values in class constants, we have a single
        source of truth for what's allowed.

        Args:
            level: Experience level to validate.

        Returns:
            True if valid, False otherwise.
        """
        return level in self.EXPERIENCE_LEVELS

    def validate_question_style(self, style: str) -> bool:
        """
        Validate a question style.

        Args:
            style: Question style to validate.

        Returns:
            True if valid, False otherwise.
        """
        return style in self.QUESTION_STYLES

    def validate_focus_area(self, area: str) -> bool:
        """
        Validate a focus area.

        Args:
            area: Focus area to validate.

        Returns:
            True if valid, False otherwise.
        """
        return area in self.FOCUS_AREAS

    def validate_model(self, model: str) -> bool:
        """
        Validate a model name.

        ⚠️ IMPORTANT: These must match Anthropic's actual model names.
        If Anthropic releases new models, update AVAILABLE_MODELS constant.

        Args:
            model: Model name to validate.

        Returns:
            True if valid, False otherwise.
        """
        return model in self.AVAILABLE_MODELS

    # ------------------------------------------------------------------------
    # MODEL CONFIGURATION
    # ------------------------------------------------------------------------

    def get_model(self) -> str:
        """
        Get the configured model.

        💡 Provides a default if model not set.
        This ensures backward compatibility if we add this field later.

        Returns:
            Model name string.
        """
        return self.get("model", "claude-sonnet-4-5")

    # ------------------------------------------------------------------------
    # LOGGING CONFIGURATION
    # ------------------------------------------------------------------------
    # 🔍 These methods encapsulate logging configuration logic

    def is_logging_enabled(self) -> bool:
        """
        Check if logging is enabled.

        Returns:
            True if logging is enabled, False otherwise.
        """
        # Default to False for privacy
        return self.get("logging.enabled", False)

    def should_log_interactions(self) -> bool:
        """
        Check if interaction logging is enabled.

        💡 Separate from is_logging_enabled() to allow granular control.
        User might want to log some things but not others.

        Returns:
            True if interaction logging is enabled, False otherwise.
        """
        # Default to True (if logging is enabled, log interactions)
        return self.get("logging.log_interactions", True)

    def should_log_api_calls(self) -> bool:
        """
        Check if API call logging is enabled.

        ⚠️ API call logging can be verbose and include sensitive data.
        Default is False for privacy and disk space.

        Returns:
            True if API call logging is enabled, False otherwise.
        """
        return self.get("logging.log_api_calls", False)


# ============================================================================
# KEY TAKEAWAYS
# ============================================================================
"""
🎓 WHAT YOU LEARNED:

1. **Configuration Manager Pattern**
   - Centralized config storage
   - Validation logic in one place
   - Clean API for accessing config

2. **Dot Notation Access**
   - Navigate nested dicts with strings like "preferences.verbosity"
   - Easier to read than config["preferences"]["verbosity"]

3. **Pathlib for File Paths**
   - Use Path() instead of os.path
   - Cleaner syntax with / operator
   - Cross-platform compatibility

4. **Default Values**
   - Always provide sensible defaults
   - Use .get(key, default) pattern
   - Makes config optional/gradual

5. **Error Handling**
   - Specific exceptions (JSONDecodeError, IOError)
   - Helpful error messages
   - Fail fast for critical issues (API key)

6. **Type Hints**
   - Dict[str, Any] documents expected types
   - Optional[Path] shows parameter can be None
   - Makes code self-documenting

7. **Class Constants**
   - Store valid options as class-level constants
   - Single source of truth
   - Easy to reference and update

📚 FURTHER LEARNING:
- JSON format specification
- Python's pathlib module
- Configuration management patterns
- Type hints and mypy
- Context managers (with statement)
"""
