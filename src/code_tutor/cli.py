"""Command-line interface for Code Tutor."""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

from .config import ConfigManager
from .cli_support import (
    ensure_configured,
    get_config_manager_from_context,
    load_config_or_raise,
)
from .logger import SessionLogger
from .exercise_manager import ExerciseManager
from .modes import COMMAND_ALIASES, get_all_modes, get_core_modes
from .proof_reader import ProofReader
from .services import (
    ProofModeService,
    ReviewModeService,
    RoguelikeModeService,
    TeachingModeService,
)


console = Console()


@click.group()
@click.version_option(version="0.1.0")
@click.option(
    "--config-dir",
    type=click.Path(),
    default=None,
    help="Custom configuration directory path",
)
@click.pass_context
def main(ctx, config_dir: Optional[str]):
    """Code Tutor - An intelligent, respectful code review and tutoring CLI tool.

    Get personalized feedback on your code that respects your experience level
    and programming style.
    """
    ctx.ensure_object(dict)
    ctx.obj["config_dir"] = config_dir


@main.command()
@click.pass_context
def setup(ctx):
    """Initial setup: configure API key and preferences."""
    console.print(Panel.fit(
        "[bold cyan]Welcome to Code Tutor![/bold cyan]\n\n"
        "Let's set up your configuration.",
        border_style="cyan",
    ))
    console.print()

    config_manager = get_config_manager_from_context(ctx)

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

    # Get provider preference (skip if API key is locked)
    if config_manager.is_api_key_locked():
        provider = existing_config.get("provider", "anthropic")
        console.print("[bold]Step 1: LLM Provider[/bold]")
        console.print(
            f"[yellow]Provider is locked with API key settings: {provider}[/yellow]\n"
        )
    else:
        existing_provider = existing_config.get("provider", "anthropic")
        provider_default_choice = "1"
        if existing_provider in {"openai", "openai_compatible", "openai-compat"}:
            provider_default_choice = "2"

        console.print("[bold]Step 1: LLM Provider[/bold]")
        console.print("[dim]Choose the backend used for AI responses.[/dim]\n")
        console.print("  1. anthropic         - Claude Messages API")
        console.print("  2. openai_compatible - OpenAI-style Chat Completions API\n")

        provider_choice = Prompt.ask(
            "Choose your provider",
            choices=["1", "2"],
            default=provider_default_choice,
        )
        provider = "anthropic" if provider_choice == "1" else "openai_compatible"

    # Get API key (skip if locked)
    if config_manager.is_api_key_locked():
        api_key = existing_config.get("api_key", "")
        if not api_key:
            console.print(
                "[red]Error: API key is locked but not configured.[/red]\n"
                "Please contact your administrator to set up the API key."
            )
            return
        console.print("[bold]Step 2: API Key[/bold]")
        console.print("[yellow]API key is locked and cannot be changed.[/yellow]\n")
    else:
        console.print("[bold]Step 2: API Key[/bold]")
        if provider == "anthropic":
            console.print(
                "[dim]Get your API key from: https://console.anthropic.com/settings/keys[/dim]\n"
            )
        else:
            console.print(
                "[dim]For OpenAI-compatible APIs, provide the provider key (e.g. OPENAI_API_KEY).[/dim]\n"
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
    console.print("\n[bold]Step 3: Model[/bold]")
    if provider == "anthropic":
        console.print("[dim]Choose which Claude model to use.[/dim]\n")
        console.print("  1. claude-opus-4-5   - Most capable, best for complex analysis")
        console.print("  2. claude-sonnet-4-5 - Balanced performance and capability (Recommended)")
        console.print("  3. claude-haiku-4-5  - Fastest and most cost-effective\n")

        default_model_choice = "2"
        existing_model = existing_config.get("model")
        if existing_model in ConfigManager.AVAILABLE_MODELS:
            default_model_choice = str(ConfigManager.AVAILABLE_MODELS.index(existing_model) + 1)

        model_choice = Prompt.ask(
            "Choose your model",
            choices=["1", "2", "3"],
            default=default_model_choice,
        )
        model = ConfigManager.AVAILABLE_MODELS[int(model_choice) - 1]
    else:
        console.print(
            "[dim]Enter an OpenAI-compatible model id (for example: gpt-4o-mini, llama3.1).[/dim]\n"
        )
        default_model = (
            existing_config.get("model")
            if existing_config.get("provider") in {"openai", "openai_compatible"}
            else ConfigManager.DEFAULT_MODELS["openai_compatible"]
        )
        model = Prompt.ask("Model", default=default_model).strip()
        if not model:
            console.print("[red]Model is required. Setup cancelled.[/red]")
            return

    # Optional base URL for openai-compatible backends
    if provider == "openai_compatible":
        console.print("\n[bold]Step 4: API Base URL[/bold]")
        console.print(
            "[dim]Use the default for OpenAI, or a custom endpoint for compatible providers.[/dim]\n"
        )
        existing_base_url = existing_config.get("base_url", "")
        base_url_default = existing_base_url or "https://api.openai.com/v1"
        base_url = Prompt.ask("Base URL", default=base_url_default).strip()
    else:
        base_url = ""

    # Get experience level
    console.print("\n[bold]Step 5: Your Programming Experience[/bold]")
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
    console.print("\n[bold]Step 6: Preferred Question Style[/bold]")
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
    console.print("\n[bold]Step 7: Focus Areas[/bold]")
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
    console.print("\n[bold]Step 8: Logging Preferences[/bold]")
    console.print("[dim]Enable logging to record student interactions for debugging.[/dim]")
    console.print("[dim]Logs may include your code and inputs on disk.[/dim]")
    console.print("[dim]Logs can be exported with 'code-tutor export-logs'[/dim]\n")

    enable_logging = Confirm.ask("Enable interaction logging?", default=False)
    redact_content = True
    log_api_calls = False
    allow_unredacted = False
    if enable_logging:
        redact_content = Confirm.ask(
            "Redact code and inputs in logs? (recommended)",
            default=True,
        )
        if not redact_content:
            console.print(
                "[yellow]Warning:[/yellow] Unredacted logs may contain sensitive code and prompts."
            )
            allow_unredacted = Confirm.ask(
                "I understand the risk and want to allow unredacted logging",
                default=False,
            )
            if not allow_unredacted:
                console.print(
                    "[yellow]Keeping redaction enabled because explicit consent was not provided.[/yellow]"
                )
                redact_content = True
        log_api_calls = Confirm.ask(
            "Log API prompts and responses?",
            default=False,
        )

    if not config_manager.validate_provider(provider):
        provider = "anthropic"

    # Save configuration
    new_config = {
        "provider": provider,
        "api_key": api_key.strip(),
        "api_key_locked": existing_config.get("api_key_locked", False),  # Preserve lock status
        "model": model,
        "base_url": base_url,
        "experience_level": experience_level,
        "preferences": {
            "question_style": question_style,
            "verbosity": "medium",
            "focus_areas": focus_areas,
        },
        "logging": {
            "enabled": enable_logging,
            "log_interactions": True,
            "log_api_calls": log_api_calls,
            "redact_content": redact_content,
            "allow_unredacted": allow_unredacted and not redact_content,
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
@click.pass_context
def review(ctx, path: str, recursive: bool):
    """Review a source code file or directory.

    PATH: Path to the file or directory to review
    """
    config_manager = get_config_manager_from_context(ctx)
    ensure_configured(config_manager)
    service = ReviewModeService(config_manager, console)
    try:
        service.review_path(path, recursive=recursive)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc


@main.command("teach-me")
@click.pass_context
def teach_me(ctx):
    """Interactive teaching mode - learn by correcting mistakes.

    In this mode, the AI presents intentionally flawed code and asks you
    to identify and explain what's wrong. This Socratic method helps you
    learn by teaching and correcting mistakes.
    """
    config_manager = get_config_manager_from_context(ctx)
    ensure_configured(config_manager)
    service = TeachingModeService(config_manager, console)
    service.start()


@main.command()
@click.pass_context
def config(ctx):
    """View or update configuration."""
    config_manager = get_config_manager_from_context(ctx)

    try:
        config_data = load_config_or_raise(config_manager)

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

        provider = config_manager.get_provider()
        console.print(f"[cyan]Provider:[/cyan] {provider}")
        console.print(f"[cyan]Model:[/cyan] {config_manager.get_model()}")
        base_url = config_manager.get_base_url() or ""
        if base_url:
            console.print(f"[cyan]Base URL:[/cyan] {base_url}")
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
        if logging_enabled:
            redact_logs = bool(logging_config.get("redact_content", True))
            if redact_logs:
                console.print("[cyan]Log redaction:[/cyan] [green]Enabled[/green]")
            else:
                consented = bool(logging_config.get("allow_unredacted", False))
                status = "[green]Confirmed[/green]" if consented else "[red]Missing[/red]"
                console.print(
                    f"[cyan]Log redaction:[/cyan] [yellow]Disabled[/yellow] "
                    f"(consent: {status})"
                )

        console.print()

        if api_key_locked:
            reconfigure_prompt = "Would you like to reconfigure non-API settings?"
        else:
            reconfigure_prompt = "Would you like to reconfigure?"

        if Confirm.ask(reconfigure_prompt, default=False):
            # Re-run setup using Click's context
            ctx.invoke(setup)

    except click.ClickException:
        raise
    except Exception as e:
        raise click.ClickException(str(e)) from e


@main.command()
def info():
    """Show information about Code Tutor."""
    core_modes_data = get_core_modes()
    core_commands = {mode.command for mode in core_modes_data}
    core_modes = "\n".join(
        f"• {mode.title} (`{mode.command}`) - {mode.summary}"
        for mode in core_modes_data
    )
    extra_modes = "\n".join(
        f"• {mode.title} (`{mode.command}`) - {mode.summary}"
        for mode in get_all_modes()
        if mode.command not in core_commands
    )
    aliases = "\n".join(
        f"• {alias} -> {target}"
        for alias, target in sorted(COMMAND_ALIASES.items())
    )

    console.print(Panel.fit(
        "[bold cyan]Code Tutor v0.1.0[/bold cyan]\n\n"
        "An intelligent, respectful code review and tutoring CLI tool.\n\n"
        "[bold]Core Modes:[/bold]\n"
        f"{core_modes}\n\n"
        "[bold]Extended Modes:[/bold]\n"
        f"{extra_modes}\n\n"
        "[bold]Features:[/bold]\n"
        "• Personalized feedback based on your experience level\n"
        "• Interactive dialogue about your code decisions\n"
        "• Respectful of your programming style and intentions\n"
        "• Persistent homework-style exercise runs\n"
        "• Mathematical proof review and teaching\n"
        "• Powered by pluggable LLM providers\n\n"
        "[bold]Commands:[/bold]\n"
        "• setup         - Configure your API key and preferences\n"
        "• review        - Review a file or directory\n"
        "• teach-me      - Learn by correcting intentionally flawed code\n"
        "• roguelike     - Generate and manage homework-style challenge runs\n"
        "• exercise      - Backwards-compatible alias for `roguelike`\n"
        "• proof         - Review mathematical proofs\n"
        "• config        - View/update configuration\n"
        "• export-logs   - Export interaction logs for debugging\n"
        "• info          - Show this information\n\n"
        "[bold]Command Aliases:[/bold]\n"
        f"{aliases}\n\n"
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
    "--clear",
    is_flag=True,
    default=False,
    help="Clear logs after exporting",
)
@click.pass_context
def export_logs(ctx, output: Optional[str], clear: bool):
    """Export student interaction logs to JSON for debugging.

    This command packages all logged student interactions into a single JSON file
    that can be sent to an instructor or developer for debugging purposes.

    Logs are only created if logging is enabled in the configuration.
    Use 'code-tutor setup' to enable logging.
    """
    config_manager = get_config_manager_from_context(ctx)

    try:
        load_config_or_raise(config_manager)

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
                '    "log_api_calls": false,\n'
                '    "redact_content": true\n'
                '  }\n'
            )

            if not Confirm.ask("\nContinue with export anyway?", default=False):
                return

        # Export logs
        console.print("\n[cyan]Exporting logs...[/cyan]\n")

        output_path = SessionLogger.export_all_logs(
            config_dir=config_manager.config_dir,
            output_path=Path(output) if output else None
        )

        console.print("[green]✓ Logs exported successfully![/green]")
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
                count = SessionLogger.clear_logs(config_manager.config_dir)
                console.print(f"[green]✓ Cleared {count} log file(s)[/green]")

        console.print("\n[dim]You can now send this file to your instructor or developer for debugging.[/dim]")

    except click.ClickException:
        raise
    except Exception as e:
        raise click.ClickException(f"Error exporting logs: {e}") from e


@main.group()
@click.pass_context
def roguelike(ctx):
    """Manage roguelike homework runs in your working directory.

    Generate, inspect, and grade challenge runs over time.
    Runs are stored in ~/code-tutor-exercises/ by default.
    """
    pass


@roguelike.command("generate")
@click.argument("topic")
@click.option(
    "--language", "-l",
    default="Python",
    help="Programming language for the exercise",
)
@click.option(
    "--type", "-t", "exercise_type",
    type=click.Choice(ExerciseManager.EXERCISE_TYPES),
    default="implementation",
    help="Type of exercise to generate",
)
@click.option(
    "--difficulty", "-d",
    type=click.Choice(["beginner", "intermediate", "advanced", "expert"]),
    default=None,
    help="Difficulty level (defaults to your experience level)",
)
@click.pass_context
def exercise_generate(ctx, topic: str, language: str, exercise_type: str, difficulty: Optional[str]):
    """Generate a new roguelike run on a topic.

    TOPIC: The concept or skill to practice (e.g., "binary search", "recursion")
    """
    config_manager = get_config_manager_from_context(ctx)
    ensure_configured(config_manager)
    service = RoguelikeModeService(config_manager)
    experience_level = config_manager.get("experience_level", "intermediate")
    resolved_difficulty = difficulty or experience_level

    console.print(Panel.fit(
        f"[bold cyan]Generating Exercise[/bold cyan]\n\n"
        f"Topic: {topic}\n"
        f"Language: {language}\n"
        f"Type: {exercise_type}\n"
        f"Difficulty: {resolved_difficulty}",
        border_style="cyan",
    ))
    console.print()

    # Generate the exercise
    console.print("[dim]Generating exercise content...[/dim]")
    try:
        result = service.generate_run(
            topic=topic,
            language=language,
            exercise_type=exercise_type,
            difficulty=resolved_difficulty,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    console.print("[dim]Creating exercise files...[/dim]")

    console.print()
    console.print("[green]Exercise created successfully![/green]")
    console.print()
    console.print(f"[cyan]Location:[/cyan] {result.exercise_info['path']}")
    console.print()
    console.print("[bold]Next steps:[/bold]")
    console.print(f"  1. Open the exercise: [cyan]cd {result.exercise_info['path']}[/cyan]")
    console.print("  2. Read the README.md for instructions")
    console.print("  3. Edit the starter file to complete the exercise")
    console.print(
        f"  4. Grade your run: [cyan]code-tutor roguelike submit {result.exercise_info['id']}[/cyan]"
    )


@roguelike.command("list")
@click.option(
    "--status", "-s",
    type=click.Choice(ExerciseManager.EXERCISE_STATUSES),
    default=None,
    help="Filter by status",
)
@click.pass_context
def exercise_list(ctx, status: Optional[str]):
    """List all stored runs in the working directory."""
    config_manager = get_config_manager_from_context(ctx)
    load_config_or_raise(config_manager)
    service = RoguelikeModeService(config_manager)
    exercises = service.list_runs(status_filter=status)

    if not exercises:
        console.print("[yellow]No exercises found.[/yellow]")
        if status:
            console.print(f"[dim]Filtered by status: {status}[/dim]")
        console.print()
        console.print("Generate a new run with:")
        console.print("  [cyan]code-tutor roguelike generate \"topic\"[/cyan]")
        return

    console.print(Panel.fit(
        f"[bold cyan]Your Roguelike Runs[/bold cyan]\n"
        f"[dim]Directory: {service.manager.exercises_dir}[/dim]",
        border_style="cyan",
    ))
    console.print()

    status_colors = {
        "pending": "yellow",
        "in_progress": "blue",
        "submitted": "magenta",
        "reviewed": "green",
        "archived": "dim",
    }

    for ex in exercises:
        metadata = ex["metadata"]
        status_str = metadata.get("status", "unknown")
        color = status_colors.get(status_str, "white")

        console.print(f"[bold]{ex['id']}[/bold]")
        console.print(f"  Topic: {metadata.get('topic', 'Unknown')}")
        console.print(f"  Language: {metadata.get('language', 'Unknown')}")
        console.print(f"  Type: {metadata.get('exercise_type', 'Unknown')}")
        console.print(f"  Status: [{color}]{status_str}[/{color}]")
        console.print(f"  Created: {metadata.get('created_at', 'Unknown')[:10]}")
        console.print()


@roguelike.command("show")
@click.argument("exercise_path")
@click.option(
    "--show-readme/--no-readme",
    default=True,
    help="Display README content inline",
)
@click.pass_context
def exercise_show(ctx, exercise_path: str, show_readme: bool):
    """Show details for a stored run so you can resume it later.

    EXERCISE_PATH: Path to the run directory or run ID.
    """
    config_manager = get_config_manager_from_context(ctx)
    load_config_or_raise(config_manager)
    service = RoguelikeModeService(config_manager)
    exercise = service.get_run(exercise_path)

    if not exercise:
        raise click.ClickException(f"Exercise not found: {exercise_path}")

    metadata = exercise["metadata"]
    console.print(Panel.fit(
        f"[bold cyan]Roguelike Run[/bold cyan]\n\n"
        f"ID: {exercise['id']}\n"
        f"Topic: {metadata.get('topic', 'Unknown')}\n"
        f"Language: {metadata.get('language', 'Unknown')}\n"
        f"Type: {metadata.get('exercise_type', 'Unknown')}\n"
        f"Difficulty: {metadata.get('difficulty', 'Unknown')}\n"
        f"Status: {metadata.get('status', 'Unknown')}\n"
        f"Path: {exercise['path']}",
        border_style="cyan",
    ))
    console.print()

    starter_file = exercise.get("starter_file")
    if starter_file:
        console.print(f"[cyan]Starter file:[/cyan] {starter_file}")

    if not show_readme:
        return

    readme_path = Path(exercise["path"]) / ExerciseManager.README_FILE
    if not readme_path.exists():
        console.print("[yellow]README.md not found for this run.[/yellow]")
        return

    readme_content = readme_path.read_text(encoding="utf-8")
    console.print()
    console.print(Panel.fit("[bold]README.md[/bold]", border_style="blue"))
    console.print()
    console.print(Markdown(readme_content))
    console.print()


def _grade_run_submission(ctx: click.Context, exercise_path: str) -> None:
    """Shared implementation for grading commands."""
    config_manager = get_config_manager_from_context(ctx)
    ensure_configured(config_manager)
    service = RoguelikeModeService(config_manager)
    exercise = service.get_run(exercise_path)

    if not exercise:
        raise click.ClickException(f"Exercise not found: {exercise_path}")

    console.print(Panel.fit(
        f"[bold cyan]Reviewing Submission[/bold cyan]\n\n"
        f"Exercise: {exercise['metadata'].get('topic', 'Unknown')}\n"
        f"Type: {exercise['metadata'].get('exercise_type', 'Unknown')}",
        border_style="cyan",
    ))
    console.print()
    console.print("[dim]Analyzing your solution...[/dim]")
    console.print()
    try:
        result = service.review_run_submission(exercise_path)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    # Display the review
    md = Markdown(result.review.feedback)
    console.print(Panel(md, border_style="green", title="Review Feedback"))

    console.print()
    console.print("[green]Exercise marked as reviewed.[/green]")


@roguelike.command("submit")
@click.argument("exercise_path")
@click.pass_context
def exercise_submit(ctx, exercise_path: str):
    """Submit a run for grading.

    EXERCISE_PATH: Path to the run directory or run ID.
    """
    _grade_run_submission(ctx, exercise_path)


@roguelike.command("grade")
@click.argument("exercise_path")
@click.pass_context
def exercise_grade(ctx, exercise_path: str):
    """Alias of submit; grade a run by ID or path."""
    _grade_run_submission(ctx, exercise_path)


@roguelike.command("hint")
@click.argument("exercise_path")
@click.pass_context
def exercise_hint(ctx, exercise_path: str):
    """Get a hint for a stored run.

    EXERCISE_PATH: Path to the run directory or run ID.

    Hints are revealed progressively. Each call reveals the next hint.
    """
    config_manager = get_config_manager_from_context(ctx)
    load_config_or_raise(config_manager)
    service = RoguelikeModeService(config_manager)
    try:
        hint_data = service.reveal_next_hint(exercise_path)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    metadata = hint_data["metadata"]

    console.print(Panel.fit(
        f"[bold cyan]Hint for: {metadata.get('topic', 'Unknown')}[/bold cyan]",
        border_style="cyan",
    ))
    console.print()

    hint = hint_data["hint"]

    if hint:
        console.print(
            f"[yellow]Hint {hint_data['revealed_index']}/{hint_data['total_hints']}:[/yellow]"
        )
        console.print()
        console.print(f"  {hint}")
        console.print()

        remaining = hint_data["remaining_hints"]
        if remaining > 0:
            console.print(f"[dim]{remaining} more hint(s) available.[/dim]")
        else:
            console.print("[dim]No more hints available.[/dim]")
    else:
        console.print("[yellow]No more hints available for this exercise.[/yellow]")
        console.print()
        console.print("If you're still stuck, try:")
        console.print("  - Re-reading the README.md instructions")
        console.print("  - Breaking the problem into smaller parts")
        console.print("  - Searching for similar examples online")

@roguelike.command("archive")
@click.argument("exercise_path")
@click.option("--force", "-f", is_flag=True, help="Archive without confirmation")
@click.pass_context
def exercise_archive(ctx, exercise_path: str, force: bool):
    """Archive a completed run.

    EXERCISE_PATH: Path to the run directory or run ID.

    Archived exercises are moved to the 'archived' subdirectory.
    """
    config_manager = get_config_manager_from_context(ctx)
    load_config_or_raise(config_manager)
    service = RoguelikeModeService(config_manager)
    exercise = service.get_run(exercise_path)

    if not exercise:
        raise click.ClickException(f"Exercise not found: {exercise_path}")

    if not force:
        if not Confirm.ask(f"Archive exercise '{exercise['id']}'?", default=False):
            console.print("[yellow]Cancelled.[/yellow]")
            return

    if service.archive_run(exercise_path):
        console.print("[green]Exercise archived successfully.[/green]")
    else:
        raise click.ClickException("Failed to archive exercise.")


for alias, target in COMMAND_ALIASES.items():
    if target == "roguelike":
        main.add_command(roguelike, name=alias)


@main.group()
@click.pass_context
def proof(ctx):
    """Review and learn about mathematical proofs.

    Get feedback on proofs written in various formats including plain text,
    LaTeX, Markdown, and formal proof assistants like Lean and Coq.
    """
    pass


@proof.command("review")
@click.argument("file_path", type=click.Path(exists=True))
@click.option(
    "--domain", "-d",
    default=None,
    help="Mathematical domain (e.g., 'real analysis', 'abstract algebra')",
)
@click.option(
    "--level", "-l",
    type=click.Choice(["student", "undergrad", "graduate", "researcher"]),
    default=None,
    help="Mathematical experience level (defaults from config)",
)
@click.pass_context
def proof_review(ctx, file_path: str, domain: Optional[str], level: Optional[str]):
    """Review a mathematical proof file.

    FILE_PATH: Path to the proof file to review

    Supported formats: .txt, .md, .tex, .lean, .v (Coq), .agda, .thy (Isabelle)
    """
    config_manager = get_config_manager_from_context(ctx)
    ensure_configured(config_manager)
    service = ProofModeService(config_manager, console)

    # Check if file type is supported
    if not service.is_supported_file(file_path):
        supported_formats = ", ".join(service.supported_formats().keys())
        raise click.ClickException(
            f"Unsupported file type.\nSupported formats: {supported_formats}"
        )

    service.review_file(file_path, domain=domain, experience_level=level)


@proof.command("teach")
@click.option(
    "--domain", "-d",
    default=None,
    help="Mathematical domain to focus on (e.g., 'real analysis')",
)
@click.pass_context
def proof_teach(ctx, domain: Optional[str]):
    """Interactive proof teaching mode - learn by finding errors.

    In this mode, the AI presents proofs with subtle errors or gaps.
    Your task is to identify what's wrong and explain the issue.

    This helps develop:
      - Critical reading of mathematical arguments
      - Understanding of common proof pitfalls
      - Ability to spot logical gaps
    """
    config_manager = get_config_manager_from_context(ctx)
    ensure_configured(config_manager)
    service = ProofModeService(config_manager, console)
    service.start_teaching(domain=domain)


@proof.command("info")
def proof_info():
    """Show information about proof review capabilities."""
    reader = ProofReader()

    console.print(Panel.fit(
        "[bold cyan]Proof Review Mode[/bold cyan]\n\n"
        "Review mathematical proofs with the same respectful,\n"
        "questioning approach as code review.\n\n"
        "[bold]Supported Formats:[/bold]",
        border_style="cyan",
    ))
    console.print()

    for ext, name in sorted(reader.SUPPORTED_EXTENSIONS.items()):
        console.print(f"  {ext:10} - {name}")

    console.print()
    console.print("[bold]Mathematical Domains:[/bold]")
    console.print()

    # Display domains in columns
    domains = reader.MATH_DOMAINS
    for i in range(0, len(domains), 3):
        row = domains[i:i+3]
        console.print("  " + "  |  ".join(f"{d:20}" for d in row))

    console.print()
    console.print("[bold]Experience Levels:[/bold]")
    console.print()
    levels = {
        "student": "Taking first proof-based course",
        "undergrad": "Undergraduate math major",
        "graduate": "Graduate student",
        "researcher": "Professional mathematician",
    }
    for level, desc in levels.items():
        console.print(f"  {level:12} - {desc}")

    console.print()
    console.print("[bold]Commands:[/bold]")
    console.print("  proof review <file>  - Review a proof file")
    console.print("  proof teach          - Practice finding errors in proofs")
    console.print()


if __name__ == "__main__":
    main()
