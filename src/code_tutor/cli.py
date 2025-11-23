"""Command-line interface for Code Tutor."""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

from .config import ConfigManager
from .session import ReviewSession
from .teaching_session import TeachingSession
from .logger import SessionLogger


console = Console()


@click.group()
@click.version_option(version="0.1.0")
def main():
    """Code Tutor - An intelligent, respectful code review and tutoring CLI tool.

    Get personalized feedback on your code that respects your experience level
    and programming style.
    """
    pass


@main.command()
@click.option(
    "--config-dir",
    type=click.Path(),
    default=None,
    help="Custom configuration directory path",
)
def setup(config_dir: Optional[str]):
    """Initial setup: configure API key and preferences."""
    console.print(Panel.fit(
        "[bold cyan]Welcome to Code Tutor![/bold cyan]\n\n"
        "Let's set up your configuration.",
        border_style="cyan",
    ))
    console.print()

    config_manager = ConfigManager(Path(config_dir) if config_dir else None)

    # Load existing config or start fresh
    try:
        existing_config = config_manager.load()
        has_existing = config_manager.is_configured()

        # Check if API key is locked
        if config_manager.is_api_key_locked():
            console.print(
                "[yellow]Configuration is locked for multi-student deployment.[/yellow]\n"
                "The API key cannot be changed. Other settings can be modified.\n"
            )
            if not Confirm.ask("Do you want to modify non-API settings?", default=False):
                console.print("[green]Setup cancelled.[/green]")
                return

        if has_existing and not config_manager.is_api_key_locked():
            console.print("[yellow]Existing configuration found.[/yellow]")
            if not Confirm.ask("Do you want to reconfigure?", default=False):
                console.print("[green]Setup cancelled. Using existing configuration.[/green]")
                return
    except Exception:
        existing_config = config_manager.DEFAULT_CONFIG.copy()

    # Get API key (skip if locked)
    if config_manager.is_api_key_locked():
        api_key = existing_config.get("api_key", "")
        if not api_key:
            console.print(
                "[red]Error: API key is locked but not configured.[/red]\n"
                "Please contact your administrator to set up the API key."
            )
            return
        console.print("[bold]Step 1: Anthropic API Key[/bold]")
        console.print("[yellow]API key is locked and cannot be changed.[/yellow]\n")
    else:
        console.print("[bold]Step 1: Anthropic API Key[/bold]")
        console.print(
            "[dim]Get your API key from: https://console.anthropic.com/settings/keys[/dim]\n"
        )

        current_key = existing_config.get("api_key", "")
        if current_key:
            api_key = Prompt.ask(
                "API Key",
                default="[hidden - press Enter to keep current]",
                password=True,
            )
            if api_key == "[hidden - press Enter to keep current]":
                api_key = current_key
        else:
            api_key = Prompt.ask("API Key", password=True)

        if not api_key or not api_key.strip():
            console.print("[red]API key is required. Setup cancelled.[/red]")
            return

    # Get model preference
    console.print("\n[bold]Step 2: Claude Model[/bold]")
    console.print("[dim]Choose which Claude model to use for code review.[/dim]\n")

    console.print("  1. claude-sonnet-4-5 - Balanced performance and capability")
    console.print("  2. claude-haiku-4-5 - Fastest and most cost-effective\n")

    model_choice = Prompt.ask(
        "Choose your model",
        choices=["1", "2"],
        default="1",
    )
    model = ConfigManager.AVAILABLE_MODELS[int(model_choice) - 1]

    # Get experience level
    console.print("\n[bold]Step 3: Your Programming Experience[/bold]")
    console.print("[dim]This helps tailor feedback to your skill level.[/dim]\n")

    for i, level in enumerate(ConfigManager.EXPERIENCE_LEVELS, 1):
        console.print(f"  {i}. {level.capitalize()}")

    experience_choice = Prompt.ask(
        "\nChoose your experience level",
        choices=["1", "2", "3", "4"],
        default="2",
    )
    experience_level = ConfigManager.EXPERIENCE_LEVELS[int(experience_choice) - 1]

    # Get question style
    console.print("\n[bold]Step 4: Preferred Question Style[/bold]")
    console.print("[dim]How would you like me to interact with you?[/dim]\n")

    console.print("  1. Socratic - Guide you to discover insights through questions")
    console.print("  2. Direct - Ask straightforward, specific questions")
    console.print("  3. Exploratory - Open-ended questions about alternatives\n")

    style_choice = Prompt.ask(
        "Choose your question style",
        choices=["1", "2", "3"],
        default="1",
    )
    question_style = ConfigManager.QUESTION_STYLES[int(style_choice) - 1]

    # Get focus areas
    console.print("\n[bold]Step 5: Focus Areas[/bold]")
    console.print("[dim]What aspects of code are most important to you?[/dim]")
    console.print("[dim]Enter numbers separated by commas (e.g., 1,2,4)[/dim]\n")

    for i, area in enumerate(ConfigManager.FOCUS_AREAS, 1):
        console.print(f"  {i}. {area.capitalize()}")

    focus_input = Prompt.ask(
        "\nChoose focus areas",
        default="1,2",
    )

    try:
        focus_indices = [int(x.strip()) - 1 for x in focus_input.split(",")]
        focus_areas = [
            ConfigManager.FOCUS_AREAS[i]
            for i in focus_indices
            if 0 <= i < len(ConfigManager.FOCUS_AREAS)
        ]
        if not focus_areas:
            focus_areas = ["design", "readability"]
    except (ValueError, IndexError):
        console.print("[yellow]Invalid input, using default focus areas.[/yellow]")
        focus_areas = ["design", "readability"]

    # Get logging preferences
    console.print("\n[bold]Step 6: Logging Preferences[/bold]")
    console.print("[dim]Enable logging to record student interactions for debugging.[/dim]")
    console.print("[dim]Logs can be exported with 'code-tutor export-logs'[/dim]\n")

    enable_logging = Confirm.ask("Enable interaction logging?", default=False)

    # Save configuration
    new_config = {
        "api_key": api_key.strip(),
        "api_key_locked": existing_config.get("api_key_locked", False),  # Preserve lock status
        "model": model,
        "experience_level": experience_level,
        "preferences": {
            "question_style": question_style,
            "verbosity": "medium",
            "focus_areas": focus_areas,
        },
        "logging": {
            "enabled": enable_logging,
            "log_interactions": True,
            "log_api_calls": False,
        },
    }

    try:
        config_manager.save(new_config)
        console.print(
            f"\n[green]✓ Configuration saved to {config_manager.config_path}[/green]"
        )
        console.print("\n[cyan]You're all set! Run 'code-tutor review <file>' to start.[/cyan]")
    except Exception as e:
        console.print(f"\n[red]Failed to save configuration: {e}[/red]")
        sys.exit(1)


@main.command()
@click.argument("path", type=click.Path(exists=True))
@click.option(
    "--recursive/--no-recursive",
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
    """Review a source code file or directory.

    PATH: Path to the file or directory to review
    """
    config_manager = ConfigManager(Path(config_dir) if config_dir else None)

    # Check if configured
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

    # Start review session
    session = ReviewSession(config_manager, console)

    path_obj = Path(path)
    if path_obj.is_file():
        session.start_review(path)
    elif path_obj.is_dir():
        session.review_directory(path, recursive=recursive)
    else:
        console.print(f"[red]Error:[/red] Invalid path: {path}")
        sys.exit(1)


@main.command("teach-me")
@click.option(
    "--config-dir",
    type=click.Path(),
    default=None,
    help="Custom configuration directory path",
)
def teach_me(config_dir: Optional[str]):
    """Interactive teaching mode - learn by correcting mistakes.

    In this mode, the AI presents intentionally flawed code and asks you
    to identify and explain what's wrong. This Socratic method helps you
    learn by teaching and correcting mistakes.
    """
    config_manager = ConfigManager(Path(config_dir) if config_dir else None)

    # Check if configured
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

    # Start teaching session
    session = TeachingSession(config_manager, console)
    session.start_session()


@main.command()
@click.option(
    "--config-dir",
    type=click.Path(),
    default=None,
    help="Custom configuration directory path",
)
@click.pass_context
def config(ctx, config_dir: Optional[str]):
    """View or update configuration."""
    config_manager = ConfigManager(Path(config_dir) if config_dir else None)

    try:
        config_data = config_manager.load()

        console.print(Panel.fit(
            "[bold]Current Configuration[/bold]",
            border_style="cyan",
        ))
        console.print()

        console.print(f"[cyan]Config file:[/cyan] {config_manager.config_path}")

        api_key = config_data.get("api_key", "")
        api_key_locked = config_data.get("api_key_locked", False)

        if api_key:
            if api_key_locked:
                # Don't reveal any characters when locked
                console.print("[cyan]API key:[/cyan] ******* [yellow](locked)[/yellow]")
            else:
                # Show partial key when unlocked
                masked = api_key[:8] + "..." if len(api_key) > 8 else "***"
                console.print(f"[cyan]API key:[/cyan] {masked}")
        else:
            console.print("[cyan]API key:[/cyan] [red]Not set[/red]")

        if api_key_locked:
            console.print(
                "[yellow]Note: API key is locked for multi-student deployment.[/yellow]"
            )

        console.print(
            f"[cyan]Model:[/cyan] {config_data.get('model', 'claude-sonnet-4-5')}"
        )
        console.print(
            f"[cyan]Experience level:[/cyan] {config_data.get('experience_level', 'Not set')}"
        )

        prefs = config_data.get("preferences", {})
        console.print(f"[cyan]Question style:[/cyan] {prefs.get('question_style', 'Not set')}")
        console.print(
            f"[cyan]Focus areas:[/cyan] {', '.join(prefs.get('focus_areas', []))}"
        )

        # Show logging settings
        logging_config = config_data.get("logging", {})
        logging_enabled = logging_config.get("enabled", False)
        console.print(
            f"[cyan]Logging:[/cyan] {'[green]Enabled[/green]' if logging_enabled else '[red]Disabled[/red]'}"
        )

        console.print()

        if api_key_locked:
            reconfigure_prompt = "Would you like to reconfigure non-API settings?"
        else:
            reconfigure_prompt = "Would you like to reconfigure?"

        if Confirm.ask(reconfigure_prompt, default=False):
            # Re-run setup using Click's context
            ctx.invoke(setup, config_dir=config_dir)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@main.command()
@click.option(
    "--config-dir",
    type=click.Path(),
    default=None,
    help="Custom configuration directory path",
)
def info(config_dir: Optional[str]):
    """Show information about Code Tutor."""
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


@main.command("export-logs")
@click.option(
    "--output",
    "-o",
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
    is_flag=True,
    default=False,
    help="Clear logs after exporting",
)
def export_logs(output: Optional[str], config_dir: Optional[str], clear: bool):
    """Export student interaction logs to JSON for debugging.

    This command packages all logged student interactions into a single JSON file
    that can be sent to an instructor or developer for debugging purposes.

    Logs are only created if logging is enabled in the configuration.
    Use 'code-tutor setup' to enable logging.
    """
    config_manager = ConfigManager(Path(config_dir) if config_dir else None)

    try:
        config_manager.load()

        # Check if logging is enabled
        if not config_manager.is_logging_enabled():
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

            if not Confirm.ask("\nContinue with export anyway?", default=False):
                return

        # Export logs
        console.print("\n[cyan]Exporting logs...[/cyan]\n")

        output_path = SessionLogger.export_all_logs(
            config_dir=config_manager.config_dir if config_dir else None,
            output_path=Path(output) if output else None
        )

        console.print(f"[green]✓ Logs exported successfully![/green]")
        console.print(f"[cyan]Output file:[/cyan] {output_path}")

        # Show summary
        import json
        with open(output_path, 'r') as f:
            data = json.load(f)
            total_sessions = data.get('total_sessions', 0)
            console.print(f"[cyan]Total sessions:[/cyan] {total_sessions}")

        # Clear logs if requested
        if clear:
            if Confirm.ask("\n[yellow]Are you sure you want to clear all log files?[/yellow]", default=False):
                count = SessionLogger.clear_logs(config_manager.config_dir if config_dir else None)
                console.print(f"[green]✓ Cleared {count} log file(s)[/green]")

        console.print("\n[dim]You can now send this file to your instructor or developer for debugging.[/dim]")

    except Exception as e:
        console.print(f"[red]Error exporting logs:[/red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
