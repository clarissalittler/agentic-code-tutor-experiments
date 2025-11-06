"""Interactive teaching mode for learning through correcting mistakes."""

from typing import Dict, List, Optional
import anthropic
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.syntax import Syntax

from .config import ConfigManager


class TeachingSession:
    """Manages an interactive teaching session using the Socratic method."""

    def __init__(self, config_manager: ConfigManager, console: Optional[Console] = None):
        """Initialize a teaching session.

        Args:
            config_manager: Configuration manager instance.
            console: Optional Rich console for formatted output.
        """
        self.config = config_manager
        self.console = console or Console()
        self.client: Optional[anthropic.Anthropic] = None
        self.model: str = ""
        self.conversation_history: List[Dict[str, str]] = []
        self.topic: str = ""
        self.round_number: int = 0
        self.max_rounds: int = 5

    def start_session(self) -> None:
        """Start an interactive teaching session."""
        try:
            # Load configuration
            config = self.config.load()
            api_key = self.config.get_api_key()
            self.model = self.config.get_model()
            experience_level = self.config.get("experience_level", "intermediate")

            # Initialize client
            self.client = anthropic.Anthropic(api_key=api_key)

            # Welcome message
            self._display_welcome()

            # Get topic from user
            self.topic = self._get_topic()

            # Get programming language preference
            language = self._get_language()

            # Start the teaching rounds
            self._run_teaching_rounds(experience_level, language)

            # Conclusion
            self._display_conclusion()

        except ValueError as e:
            self.console.print(f"[red]Error:[/red] {e}")
        except KeyboardInterrupt:
            self.console.print("\n\n[yellow]Teaching session interrupted. Goodbye![/yellow]")
        except Exception as e:
            self.console.print(f"[red]Unexpected error:[/red] {e}")

    def _display_welcome(self) -> None:
        """Display welcome message."""
        self.console.print(Panel.fit(
            "[bold cyan]Welcome to Teach Me![/bold cyan]\n\n"
            "In this mode, I'll show you code with intentional mistakes.\n"
            "Your job is to identify and explain what's wrong.\n\n"
            "The better your explanation, the more we'll learn together!\n"
            "If your explanation needs refinement, I'll adjust the code\n"
            "and we'll dig deeper into the concept.",
            border_style="cyan",
            title="🎓 Teaching Mode"
        ))
        self.console.print()

    def _get_topic(self) -> str:
        """Get the topic the user wants to learn about.

        Returns:
            The topic string.
        """
        self.console.print("[bold]What would you like to learn about?[/bold]")
        self.console.print(
            "[dim]Examples: recursion, async/await, design patterns, "
            "memory management, error handling[/dim]\n"
        )

        topic = Prompt.ask("Topic")

        self.console.print(f"\n[green]Great! Let's explore [bold]{topic}[/bold] together.[/green]\n")

        return topic

    def _get_language(self) -> str:
        """Get the preferred programming language.

        Returns:
            The language string.
        """
        self.console.print("[bold]Which programming language would you like to use?[/bold]")
        self.console.print("[dim]Examples: Python, JavaScript, Java, C++, Go, Rust[/dim]\n")

        language = Prompt.ask("Language", default="Python")

        return language

    def _run_teaching_rounds(self, experience_level: str, language: str) -> None:
        """Run the teaching rounds.

        Args:
            experience_level: User's experience level.
            language: Programming language to use.
        """
        self.round_number = 0

        while self.round_number < self.max_rounds:
            self.round_number += 1

            self.console.print(f"\n[cyan]{'='*60}[/cyan]")
            self.console.print(f"[bold cyan]Round {self.round_number}[/bold cyan]")
            self.console.print(f"[cyan]{'='*60}[/cyan]\n")

            # Generate flawed code
            code_data = self._generate_flawed_code(experience_level, language)

            if not code_data:
                self.console.print("[yellow]Failed to generate code. Ending session.[/yellow]")
                break

            # Display the code
            self._display_code(code_data["code"], language)

            # Get user's explanation
            explanation = self._get_user_explanation()

            if not explanation.strip():
                self.console.print("[yellow]Skipping this round...[/yellow]")
                continue

            # Evaluate the explanation
            evaluation = self._evaluate_explanation(
                code_data["code"],
                code_data["issues"],
                explanation,
                experience_level,
                language
            )

            # Display evaluation
            self._display_evaluation(evaluation)

            # Check if we should continue
            if evaluation.get("understanding_achieved", False):
                self.console.print(
                    "\n[green]Excellent! You've demonstrated solid understanding of this aspect.[/green]"
                )

                if not Confirm.ask("\n[cyan]Continue with another example?[/cyan]", default=True):
                    break
            else:
                self.console.print(
                    "\n[yellow]Let's refine our understanding with a related example...[/yellow]"
                )

    def _generate_flawed_code(self, experience_level: str, language: str) -> Optional[Dict]:
        """Generate code with intentional, instructive mistakes.

        Args:
            experience_level: User's experience level.
            language: Programming language.

        Returns:
            Dictionary with code and issues, or None if failed.
        """
        prompt = self._build_code_generation_prompt(experience_level, language)

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                messages=self.conversation_history + [{"role": "user", "content": prompt}],
            )

            content = response.content[0].text

            # Store in conversation history
            self.conversation_history.append({"role": "user", "content": prompt})
            self.conversation_history.append({"role": "assistant", "content": content})

            return self._parse_code_response(content)

        except Exception as e:
            self.console.print(f"[red]Error generating code:[/red] {e}")
            return None

    def _build_code_generation_prompt(self, experience_level: str, language: str) -> str:
        """Build prompt for generating flawed code.

        Args:
            experience_level: User's experience level.
            language: Programming language.

        Returns:
            The prompt string.
        """
        if self.round_number == 1:
            # First round - introduce the concept with a clear mistake
            difficulty = "obvious but instructive"
        elif self.round_number <= 3:
            # Middle rounds - more subtle mistakes
            difficulty = "subtle and thought-provoking"
        else:
            # Later rounds - nuanced mistakes
            difficulty = "nuanced and requiring deep understanding"

        return f"""You are a Socratic teacher helping a {experience_level} programmer learn about {self.topic}.

Your task: Create a SHORT code example in {language} (5-15 lines) that demonstrates a {difficulty} mistake related to {self.topic}.

The mistake should be:
1. Instructive - teaches an important concept
2. Clever - not immediately obvious
3. Realistic - something a real programmer might do
4. Focused - demonstrates ONE specific misconception

Format your response as:
## Code
```{language.lower()}
[your flawed code here]
```

## Hidden Issues
[Bullet list of what's wrong - this is for your internal tracking]
- Issue 1
- Issue 2

Remember: Make the mistake educational and thought-provoking!"""

    def _parse_code_response(self, response: str) -> Dict:
        """Parse the code generation response.

        Args:
            response: Raw response from Claude.

        Returns:
            Dictionary with code and issues.
        """
        lines = response.split("\n")
        code_lines = []
        issues = []

        in_code_block = False
        in_issues = False

        for line in lines:
            if "```" in line:
                in_code_block = not in_code_block
                continue

            if "## Hidden Issues" in line or "## Issues" in line:
                in_issues = True
                continue
            elif line.startswith("##") and in_issues:
                in_issues = False

            if in_code_block:
                code_lines.append(line)
            elif in_issues and line.strip():
                cleaned = line.lstrip("*-•").strip()
                if cleaned:
                    issues.append(cleaned)

        return {
            "code": "\n".join(code_lines),
            "issues": issues
        }

    def _display_code(self, code: str, language: str) -> None:
        """Display code with syntax highlighting.

        Args:
            code: Code to display.
            language: Programming language.
        """
        self.console.print("[bold]Here's some code for you to review:[/bold]\n")

        syntax = Syntax(code, language.lower(), theme="monokai", line_numbers=True)
        self.console.print(Panel(syntax, border_style="blue", title="Code"))
        self.console.print()

    def _get_user_explanation(self) -> str:
        """Get the user's explanation of what's wrong.

        Returns:
            The user's explanation.
        """
        self.console.print("[bold]What's wrong with this code? Please explain:[/bold]")
        self.console.print("[dim](Be specific about what the issue is and why it's a problem)[/dim]\n")

        explanation = Prompt.ask("Your explanation")

        return explanation

    def _evaluate_explanation(
        self,
        code: str,
        expected_issues: List[str],
        user_explanation: str,
        experience_level: str,
        language: str
    ) -> Dict:
        """Evaluate the user's explanation.

        Args:
            code: The flawed code.
            expected_issues: List of issues in the code.
            user_explanation: User's explanation.
            experience_level: User's experience level.
            language: Programming language.

        Returns:
            Evaluation dictionary.
        """
        prompt = f"""You are evaluating a {experience_level} programmer's understanding of {self.topic}.

Code shown:
```{language.lower()}
{code}
```

Known issues in the code:
{chr(10).join(f"- {issue}" for issue in expected_issues)}

Student's explanation:
"{user_explanation}"

Evaluate their explanation:
1. Did they identify the core issue?
2. Is their explanation technically accurate?
3. Do they understand WHY it's a problem?
4. What aspects could be explained more precisely?

Respond in this format:

## Evaluation
[Your assessment of their understanding]

## Feedback
[Constructive feedback - what they got right, what needs refinement]

## Understanding Achieved
[YES if they demonstrated solid understanding, NO if we should dig deeper]"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=self.conversation_history + [{"role": "user", "content": prompt}],
            )

            content = response.content[0].text

            # Store in history
            self.conversation_history.append({"role": "user", "content": prompt})
            self.conversation_history.append({"role": "assistant", "content": content})

            return self._parse_evaluation_response(content)

        except Exception as e:
            self.console.print(f"[red]Error evaluating explanation:[/red] {e}")
            return {"understanding_achieved": False, "feedback": "Error occurred"}

    def _parse_evaluation_response(self, response: str) -> Dict:
        """Parse the evaluation response.

        Args:
            response: Raw response from Claude.

        Returns:
            Dictionary with evaluation data.
        """
        understanding_achieved = "YES" in response.upper() and "Understanding Achieved" in response

        return {
            "understanding_achieved": understanding_achieved,
            "feedback": response
        }

    def _display_evaluation(self, evaluation: Dict) -> None:
        """Display the evaluation feedback.

        Args:
            evaluation: Evaluation dictionary.
        """
        self.console.print("\n[bold cyan]Teacher's Feedback:[/bold cyan]\n")

        md = Markdown(evaluation.get("feedback", "No feedback available"))
        self.console.print(Panel(md, border_style="green"))

    def _display_conclusion(self) -> None:
        """Display conclusion message."""
        self.console.print(f"\n\n[bold green]Teaching Session Complete![/bold green]")
        self.console.print(
            f"[dim]We completed {self.round_number} round(s) on the topic: {self.topic}[/dim]\n"
        )
        self.console.print(
            "[cyan]Remember: Teaching others is one of the best ways to learn!\n"
            "Keep practicing by explaining concepts to yourself and others.[/cyan]\n"
        )
