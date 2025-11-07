"""
Command-line interface for Code Tutor.

📚 FILE OVERVIEW:
This is the entry point for the Code Tutor application. It uses the Click
framework to create a command-line interface with multiple commands (setup,
review, teach-me, etc.). This file routes user commands to the appropriate
workflows (ReviewSession or TeachingSession).

🎯 WHAT YOU'LL LEARN:
- Click framework basics (command groups, decorators)
- Multi-step configuration wizards
- Command-line argument and option handling
- Input validation and error handling
- CLI best practices (help text, defaults, confirmations)
- Click context for command invocation

💡 WHY THIS FILE EXISTS:
Every CLI application needs an entry point that:
1. Parses command-line arguments
2. Routes to appropriate handlers
3. Provides help documentation
4. Validates inputs
5. Displays errors gracefully

This file is the "front door" to the entire application.
"""

# ============================================================================
# IMPORTS
# ============================================================================

import sys  # For sys.exit() to exit with error codes
from pathlib import Path  # Modern path handling
from typing import Optional  # Type hints

import click  # 🔍 Click framework for CLIs
from rich.console import Console  # Rich for beautiful output
from rich.panel import Panel  # Bordered panels
from rich.prompt import Prompt, Confirm  # Interactive prompts

# Our components
from .config import ConfigManager
from .session import ReviewSession
from .teaching_session import TeachingSession
from .logger import SessionLogger


# ============================================================================
# GLOBAL CONSOLE
# ============================================================================
# 💡 Create one console instance for the entire CLI
# This ensures consistent formatting across all commands

console = Console()


# ============================================================================
# MAIN COMMAND GROUP
# ============================================================================
# 🔍 Click uses decorators to define commands

@click.group()
@click.version_option(version="0.1.0")
def main():
    """
    Code Tutor - An intelligent, respectful code review and tutoring CLI tool.

    Get personalized feedback on your code that respects your experience level
    and programming style.

    💡 CLICK CONCEPTS:
    - @click.group() creates a command group (container for subcommands)
    - @click.version_option() adds --version flag automatically
    - Docstring becomes the help text (shown with --help)

    🎯 COMMAND GROUP STRUCTURE:
    main (this function)
    ├── setup
    ├── review
    ├── teach-me
    ├── config
    ├── export-logs
    └── info

    Each subcommand is defined with @main.command()
    """
    pass  # Group itself does nothing - just holds subcommands


# ============================================================================
# SETUP COMMAND
# ============================================================================

@main.command()
@click.option(
    "--config-dir",
    type=click.Path(),  # Validates path format
    default=None,
    help="Custom configuration directory path",
)
def setup(config_dir: Optional[str]):
    """
    Initial setup: configure API key and preferences.

    🔍 CLICK DECORATORS:
    - @main.command() registers this as a subcommand of main
    - @click.option() adds an optional command-line flag
    - Function docstring becomes command help text

    💡 CONFIGURATION WIZARD PATTERN:
    1. Check for existing config
    2. Ask if reconfigure (if exists)
    3. Multi-step prompts (API key, model, experience level, etc.)
    4. Build config dictionary
    5. Save to disk
    6. Display success message

    Args:
        config_dir: Optional custom configuration directory.
    """
    # ========================================
    # WELCOME MESSAGE
    # ========================================

    console.print(Panel.fit(
        "[bold cyan]Welcome to Code Tutor![/bold cyan]\n\n"
        "Let's set up your configuration.",
        border_style="cyan",
    ))
    console.print()

    # ========================================
    # INITIALIZE CONFIG MANAGER
    # ========================================
    # 🎯 Convert string to Path if provided

    config_manager = ConfigManager(Path(config_dir) if config_dir else None)

    # ========================================
    # CHECK FOR EXISTING CONFIGURATION
    # ========================================

    try:
        existing_config = config_manager.load()
        has_existing = config_manager.is_configured()

        if has_existing:
            # Config exists - ask if reconfigure
            console.print("[yellow]Existing configuration found.[/yellow]")
            if not Confirm.ask("Do you want to reconfigure?", default=False):
                console.print("[green]Setup cancelled. Using existing configuration.[/green]")
                return  # Exit early

    except Exception:
        # No config or corrupted config - start fresh
        existing_config = config_manager.DEFAULT_CONFIG.copy()

    # ========================================
    # STEP 1: API KEY
    # ========================================
    # 💡 Handle both new and existing API keys

    console.print("[bold]Step 1: Anthropic API Key[/bold]")
    console.print(
        "[dim]Get your API key from: https://console.anthropic.com/settings/keys[/dim]\n"
    )

    current_key = existing_config.get("api_key", "")

    if current_key:
        # Existing key - offer to keep it
        # 🔍 password=True hides input
        api_key = Prompt.ask(
            "API Key",
            default="[hidden - press Enter to keep current]",
            password=True,
        )

        # Check if user kept default (pressed Enter)
        if api_key == "[hidden - press Enter to keep current]":
            api_key = current_key
    else:
        # No existing key - must enter one
        api_key = Prompt.ask("API Key", password=True)

    # Validate not empty
    if not api_key or not api_key.strip():
        console.print("[red]API key is required. Setup cancelled.[/red]")
        return

    # ========================================
    # STEP 2: MODEL SELECTION
    # ========================================

    console.print("\n[bold]Step 2: Claude Model[/bold]")
    console.print("[dim]Choose which Claude model to use for code review.[/dim]\n")

    console.print("  1. claude-sonnet-4-5 - Balanced performance and capability")
    console.print("  2. claude-haiku-4-5 - Fastest and most cost-effective\n")

    # Get choice (1 or 2)
    model_choice = Prompt.ask(
        "Choose your model",
        choices=["1", "2"],  # 🔍 Only these values accepted
        default="1",
    )

    # Map choice to model name
    # 🎯 int(model_choice) - 1 converts "1" → index 0
    model = ConfigManager.AVAILABLE_MODELS[int(model_choice) - 1]

    # ========================================
    # STEP 3: EXPERIENCE LEVEL
    # ========================================

    console.print("\n[bold]Step 3: Your Programming Experience[/bold]")
    console.print("[dim]This helps tailor feedback to your skill level.[/dim]\n")

    # Display options
    # 💡 enumerate starts at 1 for user-friendly numbering
    for i, level in enumerate(ConfigManager.EXPERIENCE_LEVELS, 1):
        console.print(f"  {i}. {level.capitalize()}")

    experience_choice = Prompt.ask(
        "\nChoose your experience level",
        choices=["1", "2", "3", "4"],
        default="2",  # Default to intermediate
    )

    experience_level = ConfigManager.EXPERIENCE_LEVELS[int(experience_choice) - 1]

    # ========================================
    # STEP 4: QUESTION STYLE
    # ========================================

    console.print("\n[bold]Step 4: Preferred Question Style[/bold]")
    console.print("[dim]How would you like me to interact with you?[/dim]\n")

    console.print("  1. Socratic - Guide you to discover insights through questions")
    console.print("  2. Direct - Ask straightforward, specific questions")
    console.print("  3. Exploratory - Open-ended questions about alternatives\n")

    style_choice = Prompt.ask(
        "Choose your question style",
        choices=["1", "2", "3"],
        default="1",  # Default to Socratic
    )

    question_style = ConfigManager.QUESTION_STYLES[int(style_choice) - 1]

    # ========================================
    # STEP 5: FOCUS AREAS
    # ========================================
    # 💡 More complex - allows multiple selections

    console.print("\n[bold]Step 5: Focus Areas[/bold]")
    console.print("[dim]What aspects of code are most important to you?[/dim]")
    console.print("[dim]Enter numbers separated by commas (e.g., 1,2,4)[/dim]\n")

    # Display all options
    for i, area in enumerate(ConfigManager.FOCUS_AREAS, 1):
        console.print(f"  {i}. {area.capitalize()}")

    # Get comma-separated input
    focus_input = Prompt.ask(
        "\nChoose focus areas",
        default="1,2",
    )

    # ========================================
    # PARSE FOCUS AREAS INPUT
    # ========================================
    # 🔍 Try/except handles invalid input gracefully

    try:
        # Split by comma, strip whitespace, convert to int, subtract 1 for indexing
        focus_indices = [int(x.strip()) - 1 for x in focus_input.split(",")]

        # Build list of selected areas (with bounds checking)
        focus_areas = [
            ConfigManager.FOCUS_AREAS[i]
            for i in focus_indices
            if 0 <= i < len(ConfigManager.FOCUS_AREAS)  # Validate index
        ]

        # Fallback if empty
        if not focus_areas:
            focus_areas = ["design", "readability"]

    except (ValueError, IndexError):
        # Invalid input - use defaults
        console.print("[yellow]Invalid input, using default focus areas.[/yellow]")
        focus_areas = ["design", "readability"]

    # ========================================
    # STEP 6: LOGGING PREFERENCES
    # ========================================

    console.print("\n[bold]Step 6: Logging Preferences[/bold]")
    console.print("[dim]Enable logging to record student interactions for debugging.[/dim]")
    console.print("[dim]Logs can be exported with 'code-tutor export-logs'[/dim]\n")

    enable_logging = Confirm.ask("Enable interaction logging?", default=False)

    # ========================================
    # BUILD CONFIGURATION DICTIONARY
    # ========================================

    new_config = {
        "api_key": api_key.strip(),
        "model": model,
        "experience_level": experience_level,
        "preferences": {
            "question_style": question_style,
            "verbosity": "medium",  # Fixed value (not configurable in wizard)
            "focus_areas": focus_areas,
        },
        "logging": {
            "enabled": enable_logging,
            "log_interactions": True,  # If logging enabled, log interactions
            "log_api_calls": False,  # Don't log API calls (can be verbose)
        },
    }

    # ========================================
    # SAVE CONFIGURATION
    # ========================================

    try:
        config_manager.save(new_config)

        # Success message
        console.print(
            f"\n[green]✓ Configuration saved to {config_manager.config_path}[/green]"
        )
        console.print("\n[cyan]You're all set! Run 'code-tutor review <file>' to start.[/cyan]")

    except Exception as e:
        # Save failed
        console.print(f"\n[red]Failed to save configuration: {e}[/red]")
        sys.exit(1)  # Exit with error code


# ============================================================================
# REVIEW COMMAND
# ============================================================================

@main.command()
@click.argument("path", type=click.Path(exists=True))  # Required argument
@click.option(
    "--recursive/--no-recursive",  # Boolean flag with negation
    default=True,
    help="Recursively search directories (default: True)",
)
@click.option(
    "--config-dir",
    type=click.Path(),
    default=None,
    help="Custom configuration directory path",
)
def review(path: str, recursive: bool, config_dir: Optional[str]):
    """
    Review a source code file or directory.

    🔍 CLICK CONCEPTS:
    - @click.argument() for required positional arguments
    - @click.option() for optional flags
    - type=click.Path(exists=True) validates path exists
    - --recursive/--no-recursive creates boolean flag with negation

    💡 WORKFLOW:
    1. Load and validate configuration
    2. Create ReviewSession
    3. Check if path is file or directory
    4. Route to appropriate review method

    Args:
        path: Path to the file or directory to review (required).
        recursive: Whether to search directories recursively.
        config_dir: Optional custom config directory.

    Usage Examples:
        code-tutor review file.py
        code-tutor review src/
        code-tutor review src/ --no-recursive
        code-tutor review file.py --config-dir /custom/path
    """
    # ========================================
    # LOAD AND VALIDATE CONFIGURATION
    # ========================================

    config_manager = ConfigManager(Path(config_dir) if config_dir else None)

    try:
        config_manager.load()

        # Check if configured (has API key)
        if not config_manager.is_configured():
            console.print(
                "[red]Error:[/red] Code Tutor is not configured.\n"
                "Run 'code-tutor setup' first."
            )
            sys.exit(1)  # Exit with error code

    except Exception as e:
        console.print(f"[red]Error loading configuration:[/red] {e}")
        sys.exit(1)

    # ========================================
    # CREATE REVIEW SESSION
    # ========================================

    session = ReviewSession(config_manager, console)

    # ========================================
    # DETERMINE FILE VS DIRECTORY
    # ========================================

    path_obj = Path(path)

    if path_obj.is_file():
        # Single file review
        session.start_review(path)

    elif path_obj.is_dir():
        # Directory review
        session.review_directory(path, recursive=recursive)

    else:
        # Invalid path type
        console.print(f"[red]Error:[/red] Invalid path: {path}")
        sys.exit(1)


# ============================================================================
# TEACH-ME COMMAND
# ============================================================================

@main.command("teach-me")  # 🔍 Custom command name (hyphenated)
@click.option(
    "--config-dir",
    type=click.Path(),
    default=None,
    help="Custom configuration directory path",
)
def teach_me(config_dir: Optional[str]):
    """
    Interactive teaching mode - learn by correcting mistakes.

    In this mode, the AI presents intentionally flawed code and asks you
    to identify and explain what's wrong. This Socratic method helps you
    learn by teaching and correcting mistakes.

    💡 NAMING NOTE:
    Command name is "teach-me" (with hyphen) but function is teach_me
    (with underscore). Click automatically converts underscores to hyphens.

    Args:
        config_dir: Optional custom config directory.

    Usage:
        code-tutor teach-me
    """
    # ========================================
    # LOAD AND VALIDATE CONFIGURATION
    # ========================================
    # 🎯 Same pattern as review command

    config_manager = ConfigManager(Path(config_dir) if config_dir else None)

    try:
        config_manager.load()

        if not config_manager.is_configured():
            console.print(
                "[red]Error:[/red] Code Tutor is not configured.\n"
                "Run 'code-tutor setup' first."
            )
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]Error loading configuration:[/red] {e}")
        sys.exit(1)

    # ========================================
    # CREATE AND START TEACHING SESSION
    # ========================================

    session = TeachingSession(config_manager, console)
    session.start_session()


# ============================================================================
# CONFIG COMMAND
# ============================================================================

@main.command()
@click.option(
    "--config-dir",
    type=click.Path(),
    default=None,
    help="Custom configuration directory path",
)
@click.pass_context  # 🔍 Passes Click context to function
def config(ctx, config_dir: Optional[str]):
    """
    View or update configuration.

    🔍 CLICK CONTEXT:
    @click.pass_context passes the Click context object.
    This allows us to invoke other commands programmatically.

    💡 WORKFLOW:
    1. Display current configuration
    2. Offer to reconfigure
    3. If yes, invoke setup command

    Args:
        ctx: Click context (automatically passed).
        config_dir: Optional custom config directory.

    Usage:
        code-tutor config
    """
    # ========================================
    # LOAD CONFIGURATION
    # ========================================

    config_manager = ConfigManager(Path(config_dir) if config_dir else None)

    try:
        config_data = config_manager.load()

        # ========================================
        # DISPLAY CONFIGURATION
        # ========================================

        console.print(Panel.fit(
            "[bold]Current Configuration[/bold]",
            border_style="cyan",
        ))
        console.print()

        # Config file location
        console.print(f"[cyan]Config file:[/cyan] {config_manager.config_path}")

        # API key (masked for security)
        api_key = config_data.get("api_key", "")
        if api_key:
            # Show first 8 characters + "..."
            masked = api_key[:8] + "..." if len(api_key) > 8 else "***"
            console.print(f"[cyan]API key:[/cyan] {masked}")
        else:
            console.print("[cyan]API key:[/cyan] [red]Not set[/red]")

        # Model
        console.print(
            f"[cyan]Model:[/cyan] {config_data.get('model', 'claude-sonnet-4-5')}"
        )

        # Experience level
        console.print(
            f"[cyan]Experience level:[/cyan] {config_data.get('experience_level', 'Not set')}"
        )

        # Preferences
        prefs = config_data.get("preferences", {})
        console.print(
            f"[cyan]Question style:[/cyan] {prefs.get('question_style', 'Not set')}"
        )
        console.print(
            f"[cyan]Focus areas:[/cyan] {', '.join(prefs.get('focus_areas', []))}"
        )

        # Logging settings
        logging_config = config_data.get("logging", {})
        logging_enabled = logging_config.get("enabled", False)
        console.print(
            f"[cyan]Logging:[/cyan] "
            f"{'[green]Enabled[/green]' if logging_enabled else '[red]Disabled[/red]'}"
        )

        # ========================================
        # OFFER TO RECONFIGURE
        # ========================================

        console.print()
        if Confirm.ask("Would you like to reconfigure?", default=False):
            # Use Click context to invoke setup command
            # 🎯 ctx.invoke() calls another command programmatically
            ctx.invoke(setup, config_dir=config_dir)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


# ============================================================================
# INFO COMMAND
# ============================================================================

@main.command()
@click.option(
    "--config-dir",
    type=click.Path(),
    default=None,
    help="Custom configuration directory path",
)
def info(config_dir: Optional[str]):
    """
    Show information about Code Tutor.

    💡 SIMPLE COMMAND:
    Just displays static information about the tool.

    Args:
        config_dir: Optional custom config directory (not used, for consistency).

    Usage:
        code-tutor info
    """
    console.print(Panel.fit(
        "[bold cyan]Code Tutor v0.1.0[/bold cyan]\n\n"
        "An intelligent, respectful code review and tutoring CLI tool.\n\n"
        "[bold]Features:[/bold]\n"
        "• Personalized feedback based on your experience level\n"
        "• Interactive dialogue about your code decisions\n"
        "• Respectful of your programming style and intentions\n"
        "• Powered by Claude AI\n\n"
        "[bold]Commands:[/bold]\n"
        "• setup       - Configure your API key and preferences\n"
        "• review      - Review a file or directory\n"
        "• teach-me    - Learn by correcting intentionally flawed code\n"
        "• config      - View/update configuration\n"
        "• export-logs - Export interaction logs for debugging\n"
        "• info        - Show this information\n\n"
        "[bold]Learn more:[/bold]\n"
        "https://github.com/yourusername/code-tutor",
        border_style="cyan",
    ))


# ============================================================================
# EXPORT-LOGS COMMAND
# ============================================================================

@main.command("export-logs")
@click.option(
    "--output",
    "-o",  # Short form
    type=click.Path(),
    default=None,
    help="Output file path (default: code_tutor_logs_<timestamp>.json in current directory)",
)
@click.option(
    "--config-dir",
    type=click.Path(),
    default=None,
    help="Custom configuration directory path",
)
@click.option(
    "--clear",
    is_flag=True,  # Boolean flag (no value needed)
    default=False,
    help="Clear logs after exporting",
)
def export_logs(output: Optional[str], config_dir: Optional[str], clear: bool):
    """
    Export student interaction logs to JSON for debugging.

    This command packages all logged student interactions into a single JSON file
    that can be sent to an instructor or developer for debugging purposes.

    Logs are only created if logging is enabled in the configuration.
    Use 'code-tutor setup' to enable logging.

    🔍 CLICK FLAGS:
    - -o/--output for output path
    - --clear for boolean flag
    - is_flag=True means no value needed (presence = True)

    Args:
        output: Output file path (optional).
        config_dir: Optional custom config directory.
        clear: Whether to clear logs after export.

    Usage:
        code-tutor export-logs
        code-tutor export-logs -o logs.json
        code-tutor export-logs --clear
    """
    # ========================================
    # LOAD CONFIGURATION
    # ========================================

    config_manager = ConfigManager(Path(config_dir) if config_dir else None)

    try:
        config_manager.load()

        # ========================================
        # CHECK IF LOGGING ENABLED
        # ========================================

        if not config_manager.is_logging_enabled():
            # Logging disabled - inform user how to enable
            console.print(
                "[yellow]Logging is not currently enabled.[/yellow]\n\n"
                "To enable logging, you can manually edit your config file at:\n"
                f"  {config_manager.config_path}\n\n"
                "Add or update the following section:\n"
                '  "logging": {\n'
                '    "enabled": true,\n'
                '    "log_interactions": true,\n'
                '    "log_api_calls": false\n'
                '  }\n'
            )

            # Ask if continue anyway
            if not Confirm.ask("\nContinue with export anyway?", default=False):
                return

        # ========================================
        # EXPORT LOGS
        # ========================================

        console.print("\n[cyan]Exporting logs...[/cyan]\n")

        # Use static method from SessionLogger
        output_path = SessionLogger.export_all_logs(
            config_dir=config_manager.config_dir if config_dir else None,
            output_path=Path(output) if output else None
        )

        console.print(f"[green]✓ Logs exported successfully![/green]")
        console.print(f"[cyan]Output file:[/cyan] {output_path}")

        # ========================================
        # SHOW SUMMARY
        # ========================================

        import json
        with open(output_path, 'r') as f:
            data = json.load(f)
            total_sessions = data.get('total_sessions', 0)
            console.print(f"[cyan]Total sessions:[/cyan] {total_sessions}")

        # ========================================
        # CLEAR LOGS IF REQUESTED
        # ========================================

        if clear:
            if Confirm.ask(
                "\n[yellow]Are you sure you want to clear all log files?[/yellow]",
                default=False
            ):
                count = SessionLogger.clear_logs(
                    config_manager.config_dir if config_dir else None
                )
                console.print(f"[green]✓ Cleared {count} log file(s)[/green]")

        console.print(
            "\n[dim]You can now send this file to your instructor or developer for debugging.[/dim]"
        )

    except Exception as e:
        console.print(f"[red]Error exporting logs:[/red] {e}")
        sys.exit(1)


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    """
    Entry point when running as a script.

    💡 PYTHON IDIOM:
    if __name__ == "__main__" means "only run this when executed directly,
    not when imported as a module".

    When installed as a package, the entry point is configured in pyproject.toml:
    [tool.poetry.scripts]
    code-tutor = "code_tutor.cli:main"
    """
    main()


# ============================================================================
# KEY TAKEAWAYS
# ============================================================================
"""
🎓 WHAT YOU LEARNED:

1. **Click Framework Basics**
   - @click.group() for command groups
   - @click.command() for individual commands
   - @click.argument() for required positional args
   - @click.option() for optional flags
   - @click.pass_context for context passing

2. **Command-Line Patterns**
   - Configuration wizard with multi-step prompts
   - Path validation with click.Path(exists=True)
   - Boolean flags with --flag/--no-flag
   - Short forms with -o for --output
   - Default values and choices

3. **Configuration Wizard Design**
   - Step-by-step prompts
   - Check for existing config
   - Offer to keep or replace
   - Validate all inputs
   - Build structured config
   - Save and confirm

4. **Error Handling**
   - Try/except around config loading
   - sys.exit(1) for error exits
   - User-friendly error messages
   - Graceful degradation

5. **Click Context**
   - ctx.invoke() to call other commands
   - Allows code reuse (config → setup)
   - Passes parameters to invoked commands

6. **Input Validation**
   - choices=["1", "2", "3"] restricts input
   - Try/except for parsing errors
   - Fallback to defaults on invalid input
   - Bounds checking for list indices

7. **Help Documentation**
   - Docstrings become help text
   - --help automatically generated
   - Descriptive command and option names
   - Usage examples in docstrings

🔧 CLICK PATTERNS:

**Pattern: Command Group**
```python
@click.group()
def main():
    pass

@main.command()
def subcommand1():
    pass

@main.command()
def subcommand2():
    pass
```

**Pattern: Argument vs Option**
```python
@click.argument("required_arg")  # Positional, required
@click.option("--optional-flag", default=None)  # Named, optional
def command(required_arg, optional_flag):
    pass
```

**Pattern: Boolean Flag**
```python
@click.option("--flag/--no-flag", default=True)
def command(flag: bool):
    if flag:
        # Do something
```

**Pattern: Context Invocation**
```python
@click.pass_context
def command1(ctx):
    # Call another command
    ctx.invoke(command2, param="value")
```

📚 FURTHER LEARNING:
- Click documentation (official guide)
- CLI design best practices
- Argument parsing patterns
- User experience in CLIs
- Configuration management
- Input validation techniques
- Multi-step wizards design
"""
