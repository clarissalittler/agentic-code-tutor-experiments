"""Interactive code review session management."""

from typing import Dict, List, Optional
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

from .analyzer import CodeAnalyzer
from .config import ConfigManager
from .file_reader import FileReader


class ReviewSession:
    """Manages an interactive code review session."""

    def __init__(self, config_manager: ConfigManager, console: Optional[Console] = None):
        """Initialize a review session.

        Args:
            config_manager: Configuration manager instance.
            console: Optional Rich console for formatted output.
        """
        self.config = config_manager
        self.console = console or Console()
        self.file_reader = FileReader()
        self.analyzer: Optional[CodeAnalyzer] = None

    def start_review(self, file_path: str) -> None:
        """Start an interactive code review session.

        Args:
            file_path: Path to the file to review.
        """
        try:
            # Load configuration
            config = self.config.load()
            api_key = self.config.get_api_key()
            experience_level = self.config.get("experience_level", "intermediate")
            preferences = self.config.get("preferences", {})

            # Initialize analyzer
            self.analyzer = CodeAnalyzer(api_key)

            # Read the file
            self.console.print(f"\n[cyan]Reading file:[/cyan] {file_path}")
            file_data = self.file_reader.read_file(file_path)

            metadata = file_data["metadata"]
            self.console.print(
                f"[dim]Language: {metadata['language']} | "
                f"Lines: {metadata['line_count']} | "
                f"Size: {metadata['size_bytes']} bytes[/dim]\n"
            )

            # Perform initial analysis
            self.console.print("[cyan]Analyzing code...[/cyan]")
            analysis = self.analyzer.analyze_code(
                file_data["content"],
                metadata,
                experience_level,
                preferences,
            )

            # Display initial observations
            if analysis.get("observations"):
                self._display_observations(analysis["observations"])

            # Ask questions
            questions = analysis.get("questions", [])
            if questions:
                answers = self._ask_questions(questions)

                # Get feedback based on answers
                self.console.print("\n[cyan]Generating personalized feedback...[/cyan]\n")
                feedback_data = self.analyzer.process_answers(
                    answers, experience_level, preferences
                )

                self._display_feedback(feedback_data["feedback"])

                # Offer follow-up conversation
                self._follow_up_conversation()
            else:
                self.console.print(
                    "[yellow]No questions generated. This might indicate an issue.[/yellow]"
                )

        except FileNotFoundError as e:
            self.console.print(f"[red]Error:[/red] {e}")
        except ValueError as e:
            self.console.print(f"[red]Error:[/red] {e}")
        except Exception as e:
            self.console.print(f"[red]Unexpected error:[/red] {e}")

    def _display_observations(self, observations: List[str]) -> None:
        """Display initial observations.

        Args:
            observations: List of observation strings.
        """
        self.console.print(Panel.fit(
            "[bold]Initial Observations[/bold]\n\n" +
            "\n".join(f"• {obs}" for obs in observations),
            border_style="blue",
        ))
        self.console.print()

    def _ask_questions(self, questions: List[str]) -> List[str]:
        """Ask the user questions and collect answers.

        Args:
            questions: List of questions to ask.

        Returns:
            List of user's answers.
        """
        self.console.print(Panel.fit(
            "[bold]I have some questions about your code[/bold]\n\n" +
            "Please help me understand your design decisions:",
            border_style="cyan",
        ))
        self.console.print()

        answers = []
        for i, question in enumerate(questions, 1):
            self.console.print(f"[bold cyan]Question {i}:[/bold cyan] {question}\n")
            answer = Prompt.ask("[dim]Your answer[/dim]")
            answers.append(answer)
            self.console.print()

        return answers

    def _display_feedback(self, feedback: str) -> None:
        """Display feedback using rich formatting.

        Args:
            feedback: Feedback text (markdown formatted).
        """
        self.console.print(Panel.fit(
            "[bold green]Feedback & Suggestions[/bold green]",
            border_style="green",
        ))
        self.console.print()

        # Render as markdown
        md = Markdown(feedback)
        self.console.print(md)
        self.console.print()

    def _follow_up_conversation(self) -> None:
        """Allow user to ask follow-up questions."""
        self.console.print(
            "[dim]You can now ask follow-up questions, or press Ctrl+C to exit.[/dim]\n"
        )

        try:
            while True:
                wants_followup = Confirm.ask(
                    "[cyan]Do you have any follow-up questions?[/cyan]",
                    default=False,
                )

                if not wants_followup:
                    self.console.print("\n[green]Review session complete! Happy coding! 🎉[/green]")
                    break

                question = Prompt.ask("\n[bold]Your question[/bold]")
                if not question.strip():
                    continue

                self.console.print("\n[cyan]Thinking...[/cyan]\n")
                response = self.analyzer.continue_conversation(question)

                md = Markdown(response)
                self.console.print(Panel(md, border_style="blue"))
                self.console.print()

        except KeyboardInterrupt:
            self.console.print("\n\n[yellow]Session interrupted. Goodbye![/yellow]")

    def review_directory(self, directory: str, recursive: bool = True) -> None:
        """Review multiple files in a directory.

        Args:
            directory: Directory path to review.
            recursive: Whether to search recursively.
        """
        try:
            files = self.file_reader.find_files(directory, recursive)

            if not files:
                self.console.print(
                    f"[yellow]No supported source files found in {directory}[/yellow]"
                )
                return

            self.console.print(f"\n[cyan]Found {len(files)} file(s) to review:[/cyan]")
            for i, file in enumerate(files, 1):
                self.console.print(f"  {i}. {file}")

            self.console.print()
            proceed = Confirm.ask("Review all files?", default=False)

            if not proceed:
                # Let user select specific files
                selection = Prompt.ask(
                    "Enter file numbers to review (comma-separated) or 'all'",
                    default="all"
                )

                if selection.lower() != "all":
                    try:
                        indices = [int(x.strip()) - 1 for x in selection.split(",")]
                        files = [files[i] for i in indices if 0 <= i < len(files)]
                    except (ValueError, IndexError):
                        self.console.print("[red]Invalid selection[/red]")
                        return

            # Review each file
            for i, file in enumerate(files, 1):
                self.console.print(f"\n[bold cyan]{'='*60}[/bold cyan]")
                self.console.print(f"[bold cyan]Reviewing file {i}/{len(files)}[/bold cyan]")
                self.console.print(f"[bold cyan]{'='*60}[/bold cyan]")

                self.start_review(file)

                if i < len(files):
                    self.console.print()
                    if not Confirm.ask("Continue to next file?", default=True):
                        break

                # Reset analyzer for next file
                if self.analyzer:
                    self.analyzer.reset_conversation()

        except Exception as e:
            self.console.print(f"[red]Error:[/red] {e}")
