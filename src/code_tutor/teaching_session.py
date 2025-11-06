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
            "In this mode, I'll roleplay as a student who's stuck on some code.\n"
            "I'll show you what I tried, what went wrong, and ask for your help.\n\n"
            "As the teacher, guide me with hints and questions rather than\n"
            "giving away the answer directly. Help me discover the solution myself!\n\n"
            "The better your hints, the more we'll both learn together!",
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

            # Display the code and student question
            self._display_code(code_data["code"], code_data.get("student_question", ""), language)

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
                    "\n[green]Great teaching! The student has reached understanding through your hints.[/green]"
                )

                if not Confirm.ask("\n[cyan]Help another student with a new problem?[/cyan]", default=True):
                    break
            else:
                self.console.print(
                    "\n[yellow]The student needs more guidance. Let's try another related example...[/yellow]"
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

        return f"""You are roleplaying as a {experience_level} programmer student who needs help with {self.topic}.

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

## Student Question
[Write a short, authentic message from the student perspective. Include:
- What they were trying to accomplish
- What happened when they ran it (error message, unexpected output, or weird behavior)
- A specific question asking for help
Example: "I tried running this code to X, but I got this error: [error message]. Can you help me understand what's going wrong?"]

## Hidden Issues
[Bullet list of what's wrong - this is for your internal tracking]
- Issue 1
- Issue 2

Remember: Make the student question authentic and include helpful hints like error messages or unexpected behavior!"""

    def _parse_code_response(self, response: str) -> Dict:
        """Parse the code generation response.

        Args:
            response: Raw response from Claude.

        Returns:
            Dictionary with code, student_question, and issues.
        """
        lines = response.split("\n")
        code_lines = []
        student_question_lines = []
        issues = []

        in_code_block = False
        in_student_question = False
        in_issues = False

        for line in lines:
            if "```" in line:
                in_code_block = not in_code_block
                continue

            if "## Student Question" in line:
                in_student_question = True
                in_issues = False
                continue
            elif "## Hidden Issues" in line or "## Issues" in line:
                in_issues = True
                in_student_question = False
                continue
            elif line.startswith("##"):
                in_student_question = False
                if in_issues:
                    in_issues = False

            if in_code_block:
                code_lines.append(line)
            elif in_student_question and line.strip():
                student_question_lines.append(line.strip())
            elif in_issues and line.strip():
                cleaned = line.lstrip("*-•").strip()
                if cleaned:
                    issues.append(cleaned)

        return {
            "code": "\n".join(code_lines),
            "student_question": " ".join(student_question_lines),
            "issues": issues
        }

    def _display_code(self, code: str, student_question: str, language: str) -> None:
        """Display code with syntax highlighting and student's question.

        Args:
            code: Code to display.
            student_question: The student's question about the code.
            language: Programming language.
        """
        # Display student's question in a speech bubble style
        self.console.print(Panel.fit(
            f"[italic]{student_question}[/italic]",
            border_style="yellow",
            title="🧑‍💻 Student Question",
            subtitle="(What hints can you give?)"
        ))
        self.console.print()

        # Display the code
        syntax = Syntax(code, language.lower(), theme="monokai", line_numbers=True)
        self.console.print(Panel(syntax, border_style="blue", title="Student's Code"))
        self.console.print()

    def _get_user_explanation(self) -> str:
        """Get the user's teaching response with hints.

        Returns:
            The user's hints and guidance.
        """
        self.console.print("[bold]How will you guide this student? Provide hints:[/bold]")
        self.console.print(
            "[dim]Give hints, ask leading questions, or point them in the right direction.\n"
            "Remember: Don't just give the answer - help them discover it![/dim]\n"
        )

        explanation = Prompt.ask("Your teaching response")

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
        prompt = f"""You are roleplaying as a {experience_level} programmer student learning about {self.topic}. The user is acting as your teacher.

You showed this code:
```{language.lower()}
{code}
```

Known issues in the code:
{chr(10).join(f"- {issue}" for issue in expected_issues)}

Teacher's hints/guidance:
"{user_explanation}"

Evaluate the teacher's hints:
1. Did they give helpful hints without revealing the full answer?
2. Were the hints specific enough to guide you toward the solution?
3. Did they ask good guiding questions that promote discovery?
4. How well did they balance between being helpful and letting you learn?

Respond as the student, staying in character:

## Student Response
[React to their hints. If the hints were good, show you're getting closer to understanding. If they directly gave the answer, acknowledge you got it but note it would have been better to discover it yourself. If hints were too vague, ask for clarification.]

## Teaching Quality Assessment
[Brief internal note on teaching quality: Were the hints appropriately scaffolded? Did they promote active learning?]

## Understanding Achieved
[YES if the student has reached understanding through good hints, NO if more scaffolding is needed]"""

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
        self.console.print("\n[bold yellow]Student's Response:[/bold yellow]\n")

        md = Markdown(evaluation.get("feedback", "No feedback available"))
        self.console.print(Panel(md, border_style="green", title="🧑‍💻 After Your Hints"))

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
