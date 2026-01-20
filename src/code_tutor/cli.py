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
from .exercise_manager import ExerciseManager
from .exercise_generator import ExerciseGenerator
from .proof_reader import ProofReader
from .proof_session import ProofSession, ProofTeachingSession


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
    config_dir = ctx.obj.get("config_dir")
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
@click.pass_context
def review(ctx, path: str, recursive: bool):
    """Review a source code file or directory.

    PATH: Path to the file or directory to review
    """
    config_dir = ctx.obj.get("config_dir")
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
@click.pass_context
def teach_me(ctx):
    """Interactive teaching mode - learn by correcting mistakes.

    In this mode, the AI presents intentionally flawed code and asks you
    to identify and explain what's wrong. This Socratic method helps you
    learn by teaching and correcting mistakes.
    """
    config_dir = ctx.obj.get("config_dir")
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
@click.pass_context
def config(ctx):
    """View or update configuration."""
    config_dir = ctx.obj.get("config_dir")
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
            ctx.invoke(setup)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@main.command()
def info():
    """Show information about Code Tutor."""
    console.print(Panel.fit(
        "[bold cyan]Code Tutor v0.1.0[/bold cyan]\n\n"
        "An intelligent, respectful code review and tutoring CLI tool.\n\n"
        "[bold]Features:[/bold]\n"
        "• Personalized feedback based on your experience level\n"
        "• Interactive dialogue about your code decisions\n"
        "• Respectful of your programming style and intentions\n"
        "• Practice exercises with working directory\n"
        "• Mathematical proof review and teaching\n"
        "• Powered by Claude AI\n\n"
        "[bold]Commands:[/bold]\n"
        "• setup         - Configure your API key and preferences\n"
        "• review        - Review a file or directory\n"
        "• teach-me      - Learn by correcting intentionally flawed code\n"
        "• exercise      - Generate and manage coding exercises\n"
        "• proof         - Review mathematical proofs\n"
        "• config        - View/update configuration\n"
        "• export-logs   - Export interaction logs for debugging\n"
        "• info          - Show this information\n\n"
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
    config_dir = ctx.obj.get("config_dir")
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


@main.group()
@click.pass_context
def exercise(ctx):
    """Manage coding exercises in your working directory.

    Generate, list, and submit exercises for practice and review.
    Exercises are stored in ~/code-tutor-exercises/ by default.
    """
    pass


@exercise.command("generate")
@click.argument("topic")
@click.option(
    "--language", "-l",
    default="Python",
    help="Programming language for the exercise",
)
@click.option(
    "--type", "-t", "exercise_type",
    type=click.Choice([
        "fill_in_blank", "bug_fix", "implementation", "refactoring", "test_writing"
    ]),
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
    """Generate a new exercise on a topic.

    TOPIC: The concept or skill to practice (e.g., "binary search", "recursion")
    """
    config_dir = ctx.obj.get("config_dir")
    config_manager = ConfigManager(Path(config_dir) if config_dir else None)

    try:
        config_manager.load()
        if not config_manager.is_configured():
            console.print(
                "[red]Error:[/red] Code Tutor is not configured.\n"
                "Run 'code-tutor setup' first."
            )
            sys.exit(1)

        api_key = config_manager.get_api_key()
        model = config_manager.get_model()
        experience_level = config_manager.get("experience_level", "intermediate")

        # Use experience level as default difficulty
        if difficulty is None:
            difficulty = experience_level

        console.print(Panel.fit(
            f"[bold cyan]Generating Exercise[/bold cyan]\n\n"
            f"Topic: {topic}\n"
            f"Language: {language}\n"
            f"Type: {exercise_type}\n"
            f"Difficulty: {difficulty}",
            border_style="cyan",
        ))
        console.print()

        # Generate the exercise
        console.print("[dim]Generating exercise content...[/dim]")

        generator = ExerciseGenerator(api_key, model)
        exercise_content = generator.generate_exercise(
            topic=topic,
            language=language,
            exercise_type=exercise_type,
            difficulty=difficulty,
            experience_level=experience_level,
        )

        # Create the exercise in the working directory
        console.print("[dim]Creating exercise files...[/dim]")

        manager = ExerciseManager(config_manager=config_manager)
        exercise_info = manager.create_exercise(
            topic=topic,
            language=language,
            exercise_type=exercise_type,
            difficulty=difficulty,
            instructions=exercise_content.get("instructions", ""),
            starter_code=exercise_content.get("starter_code", ""),
            solution_hints=exercise_content.get("hints", []),
            learning_objectives=exercise_content.get("learning_objectives", []),
            test_code=exercise_content.get("test_code", None),
        )

        console.print()
        console.print(f"[green]Exercise created successfully![/green]")
        console.print()
        console.print(f"[cyan]Location:[/cyan] {exercise_info['path']}")
        console.print()
        console.print("[bold]Next steps:[/bold]")
        console.print(f"  1. Open the exercise: [cyan]cd {exercise_info['path']}[/cyan]")
        console.print(f"  2. Read the README.md for instructions")
        console.print(f"  3. Edit the starter file to complete the exercise")
        console.print(f"  4. Submit for review: [cyan]code-tutor exercise submit {exercise_info['id']}[/cyan]")

    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        sys.exit(1)


@exercise.command("list")
@click.option(
    "--status", "-s",
    type=click.Choice(["pending", "in_progress", "submitted", "reviewed", "archived"]),
    default=None,
    help="Filter by status",
)
@click.pass_context
def exercise_list(ctx, status: Optional[str]):
    """List all exercises in the working directory."""
    config_dir = ctx.obj.get("config_dir")
    config_manager = ConfigManager(Path(config_dir) if config_dir else None)
    config_manager.load()

    manager = ExerciseManager(config_manager=config_manager)
    exercises = manager.list_exercises(status_filter=status)

    if not exercises:
        console.print("[yellow]No exercises found.[/yellow]")
        if status:
            console.print(f"[dim]Filtered by status: {status}[/dim]")
        console.print()
        console.print("Generate a new exercise with:")
        console.print("  [cyan]code-tutor exercise generate \"topic\"[/cyan]")
        return

    console.print(Panel.fit(
        f"[bold cyan]Your Exercises[/bold cyan]\n"
        f"[dim]Directory: {manager.exercises_dir}[/dim]",
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


@exercise.command("submit")
@click.argument("exercise_path")
@click.pass_context
def exercise_submit(ctx, exercise_path: str):
    """Submit an exercise for review.

    EXERCISE_PATH: Path to the exercise directory or exercise ID
    """
    config_dir = ctx.obj.get("config_dir")
    config_manager = ConfigManager(Path(config_dir) if config_dir else None)

    try:
        config_manager.load()
        if not config_manager.is_configured():
            console.print(
                "[red]Error:[/red] Code Tutor is not configured.\n"
                "Run 'code-tutor setup' first."
            )
            sys.exit(1)

        manager = ExerciseManager(config_manager=config_manager)
        exercise = manager.get_exercise(exercise_path)

        if not exercise:
            console.print(f"[red]Error:[/red] Exercise not found: {exercise_path}")
            sys.exit(1)

        # Read the submitted code
        starter_file = exercise.get("starter_file")
        if not starter_file:
            console.print("[red]Error:[/red] Could not find starter file in exercise.")
            sys.exit(1)

        with open(starter_file, "r") as f:
            submitted_code = f.read()

        console.print(Panel.fit(
            f"[bold cyan]Reviewing Submission[/bold cyan]\n\n"
            f"Exercise: {exercise['metadata'].get('topic', 'Unknown')}\n"
            f"Type: {exercise['metadata'].get('exercise_type', 'Unknown')}",
            border_style="cyan",
        ))
        console.print()
        console.print("[dim]Analyzing your solution...[/dim]")
        console.print()

        # Review the submission
        api_key = config_manager.get_api_key()
        model = config_manager.get_model()
        experience_level = config_manager.get("experience_level", "intermediate")

        generator = ExerciseGenerator(api_key, model)
        review = generator.review_submission(
            original_exercise=exercise["metadata"],
            submitted_code=submitted_code,
            language=exercise["metadata"].get("language", "Python"),
            experience_level=experience_level,
        )

        # Display the review
        from rich.markdown import Markdown
        md = Markdown(review.get("feedback", "No feedback available."))
        console.print(Panel(md, border_style="green", title="Review Feedback"))

        # Update status
        manager.update_status(exercise_path, ExerciseManager.STATUS_REVIEWED)
        console.print()
        console.print(f"[green]Exercise marked as reviewed.[/green]")

    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        sys.exit(1)


@exercise.command("hint")
@click.argument("exercise_path")
@click.pass_context
def exercise_hint(ctx, exercise_path: str):
    """Get a hint for an exercise.

    EXERCISE_PATH: Path to the exercise directory or exercise ID

    Hints are revealed progressively. Each call reveals the next hint.
    """
    config_dir = ctx.obj.get("config_dir")
    config_manager = ConfigManager(Path(config_dir) if config_dir else None)
    config_manager.load()

    manager = ExerciseManager(config_manager=config_manager)
    exercise = manager.get_exercise(exercise_path)

    if not exercise:
        console.print(f"[red]Error:[/red] Exercise not found: {exercise_path}")
        sys.exit(1)

    metadata = exercise["metadata"]
    hints = metadata.get("solution_hints", [])
    revealed = metadata.get("hints_revealed", 0)

    console.print(Panel.fit(
        f"[bold cyan]Hint for: {metadata.get('topic', 'Unknown')}[/bold cyan]",
        border_style="cyan",
    ))
    console.print()

    hint = manager.get_next_hint(exercise_path)

    if hint:
        console.print(f"[yellow]Hint {revealed + 1}/{len(hints)}:[/yellow]")
        console.print()
        console.print(f"  {hint}")
        console.print()

        remaining = len(hints) - (revealed + 1)
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

    # Update status to in_progress if it was pending
    if metadata.get("status") == ExerciseManager.STATUS_PENDING:
        manager.update_status(exercise_path, ExerciseManager.STATUS_IN_PROGRESS)


@exercise.command("archive")
@click.argument("exercise_path")
@click.option("--force", "-f", is_flag=True, help="Archive without confirmation")
@click.pass_context
def exercise_archive(ctx, exercise_path: str, force: bool):
    """Archive a completed exercise.

    EXERCISE_PATH: Path to the exercise directory or exercise ID

    Archived exercises are moved to the 'archived' subdirectory.
    """
    config_dir = ctx.obj.get("config_dir")
    config_manager = ConfigManager(Path(config_dir) if config_dir else None)
    config_manager.load()

    manager = ExerciseManager(config_manager=config_manager)
    exercise = manager.get_exercise(exercise_path)

    if not exercise:
        console.print(f"[red]Error:[/red] Exercise not found: {exercise_path}")
        sys.exit(1)

    if not force:
        if not Confirm.ask(f"Archive exercise '{exercise['id']}'?", default=False):
            console.print("[yellow]Cancelled.[/yellow]")
            return

    if manager.archive_exercise(exercise_path):
        console.print(f"[green]Exercise archived successfully.[/green]")
    else:
        console.print(f"[red]Failed to archive exercise.[/red]")
        sys.exit(1)


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
    config_dir = ctx.obj.get("config_dir")
    config_manager = ConfigManager(Path(config_dir) if config_dir else None)

    try:
        config_manager.load()
        if not config_manager.is_configured():
            console.print(
                "[red]Error:[/red] Code Tutor is not configured.\n"
                "Run 'code-tutor setup' first."
            )
            sys.exit(1)

        # Check if file type is supported
        reader = ProofReader()
        if not reader.is_supported(file_path):
            console.print(f"[red]Error:[/red] Unsupported file type.")
            console.print(f"Supported formats: {', '.join(reader.SUPPORTED_EXTENSIONS.keys())}")
            sys.exit(1)

        # Start proof review session
        session = ProofSession(config_manager, console)
        session.start_review(file_path, domain=domain, experience_level=level)

    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        sys.exit(1)


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
    config_dir = ctx.obj.get("config_dir")
    config_manager = ConfigManager(Path(config_dir) if config_dir else None)

    try:
        config_manager.load()
        if not config_manager.is_configured():
            console.print(
                "[red]Error:[/red] Code Tutor is not configured.\n"
                "Run 'code-tutor setup' first."
            )
            sys.exit(1)

        # Start proof teaching session
        session = ProofTeachingSession(config_manager, console)
        session.start_session(domain=domain)

    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        sys.exit(1)


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
