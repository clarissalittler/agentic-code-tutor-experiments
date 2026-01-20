"""Interactive proof review session management."""

from typing import Dict, List, Optional, Any
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.syntax import Syntax

from .config import ConfigManager
from .proof_reader import ProofReader
from .proof_analyzer import ProofAnalyzer
from .logger import SessionLogger


class ProofSession:
    """Manages an interactive proof review session."""

    def __init__(self, config_manager: ConfigManager, console: Optional[Console] = None):
        """Initialize a proof review session.

        Args:
            config_manager: Configuration manager instance.
            console: Optional Rich console for formatted output.
        """
        self.config = config_manager
        self.console = console or Console()
        self.reader = ProofReader()
        self.analyzer: Optional[ProofAnalyzer] = None
        self.current_proof: Optional[Dict[str, Any]] = None

        # Initialize logger if enabled
        self.logger: Optional[SessionLogger] = None
        if self.config.is_logging_enabled():
            self.logger = SessionLogger(
                config_dir=self.config.config_dir,
                enabled=True
            )

    def start_review(
        self,
        file_path: str,
        domain: Optional[str] = None,
        experience_level: Optional[str] = None,
    ) -> None:
        """Start a proof review session.

        Args:
            file_path: Path to the proof file to review.
            domain: Optional mathematical domain context.
            experience_level: Optional experience level override.
        """
        try:
            # Load configuration
            config = self.config.load()
            api_key = self.config.get_api_key()
            model = self.config.get_model()

            # Use code experience level mapped to proof levels
            code_level = self.config.get("experience_level", "intermediate")
            if experience_level is None:
                # Map code experience to proof experience
                level_map = {
                    "beginner": "student",
                    "intermediate": "undergrad",
                    "advanced": "graduate",
                    "expert": "researcher",
                }
                experience_level = level_map.get(code_level, "undergrad")

            preferences = self.config.get("preferences", {})

            # Initialize analyzer
            self.analyzer = ProofAnalyzer(api_key=api_key, model=model)

            # Read the proof file
            self.console.print(f"[dim]Reading proof from {file_path}...[/dim]\n")

            try:
                self.current_proof = self.reader.read_file(file_path)
            except FileNotFoundError:
                self.console.print(f"[red]Error:[/red] File not found: {file_path}")
                return
            except ValueError as e:
                self.console.print(f"[red]Error:[/red] {e}")
                return

            # Start session logging
            if self.logger:
                self.logger.start_session("proof_review", {
                    "file": file_path,
                    "format": self.current_proof["metadata"]["format"],
                    "domain": domain or self.current_proof["metadata"].get("detected_domain"),
                    "experience_level": experience_level,
                    "model": model,
                })

            # Display proof info
            self._display_proof_info(domain)

            # Analyze the proof
            self._analyze_and_question(experience_level, domain, preferences)

            # Handle follow-up conversation
            self._follow_up_loop()

            # End session logging
            if self.logger:
                self.logger.end_session()

        except ValueError as e:
            if self.logger:
                self.logger.log_error("ValueError", str(e))
            self.console.print(f"[red]Error:[/red] {e}")
        except KeyboardInterrupt:
            if self.logger:
                self.logger.end_session()
            self.console.print("\n\n[yellow]Review session interrupted. Goodbye![/yellow]")
        except Exception as e:
            if self.logger:
                import traceback
                self.logger.log_error("UnexpectedException", str(e), traceback.format_exc())
            self.console.print(f"[red]Unexpected error:[/red] {e}")

    def _display_proof_info(self, domain: Optional[str]) -> None:
        """Display information about the loaded proof.

        Args:
            domain: Optional domain override.
        """
        metadata = self.current_proof["metadata"]
        structure = self.current_proof["structure"]

        detected = metadata.get("detected_domain", "Not detected")
        domain_display = domain if domain else detected

        techniques = ", ".join(structure.get("proof_techniques", [])) or "None detected"

        info = (
            f"[bold cyan]Proof Review[/bold cyan]\n\n"
            f"File: {self.current_proof['name']}\n"
            f"Format: {metadata['format']}\n"
            f"Lines: {metadata['line_count']}\n"
            f"Domain: {domain_display}\n"
            f"Detected techniques: {techniques}"
        )

        if metadata.get("is_formal"):
            info += "\n[yellow]Formal proof assistant detected[/yellow]"

        self.console.print(Panel.fit(info, border_style="cyan"))
        self.console.print()

        # Display the proof content
        self._display_proof_content()

    def _display_proof_content(self) -> None:
        """Display the proof content with appropriate formatting."""
        metadata = self.current_proof["metadata"]
        content = self.current_proof["content"]

        # Choose syntax highlighting based on format
        lexer_map = {
            "LaTeX": "latex",
            "Lean": "lean",
            "Lean 4": "lean4",
            "Coq": "coq",
            "Agda": "agda",
            "Markdown": "markdown",
            "Plain Text": "text",
        }

        lexer = lexer_map.get(metadata["format"], "text")

        # Truncate very long proofs for display
        lines = content.split("\n")
        if len(lines) > 100:
            display_content = "\n".join(lines[:50]) + "\n\n... [truncated for display] ...\n\n" + "\n".join(lines[-20:])
            self.console.print("[dim]Note: Proof truncated for display. Full content will be analyzed.[/dim]\n")
        else:
            display_content = content

        syntax = Syntax(display_content, lexer, theme="monokai", line_numbers=True)
        self.console.print(Panel(syntax, border_style="blue", title="Proof Content"))
        self.console.print()

    def _analyze_and_question(
        self,
        experience_level: str,
        domain: Optional[str],
        preferences: Dict,
    ) -> None:
        """Analyze the proof and ask clarifying questions.

        Args:
            experience_level: User's experience level.
            domain: Mathematical domain.
            preferences: User preferences.
        """
        self.console.print("[dim]Analyzing proof...[/dim]\n")

        try:
            analysis = self.analyzer.analyze_proof(
                content=self.current_proof["content"],
                file_metadata=self.current_proof["metadata"],
                structure=self.current_proof["structure"],
                experience_level=experience_level,
                domain=domain,
                preferences=preferences,
            )
        except ValueError as e:
            self.console.print(f"[red]Analysis failed:[/red] {e}")
            return

        # Display main claim
        if analysis.get("main_claim"):
            self.console.print(Panel.fit(
                f"[bold]Main Claim:[/bold] {analysis['main_claim']}",
                border_style="green",
            ))
            self.console.print()

        # Display observations
        if analysis.get("observations"):
            self.console.print("[bold cyan]Initial Observations:[/bold cyan]\n")
            for obs in analysis["observations"]:
                self.console.print(f"  • {obs}")
            self.console.print()

        # Ask questions
        questions = analysis.get("questions", [])
        if not questions:
            self.console.print("[yellow]No clarifying questions generated.[/yellow]")
            return

        self.console.print("[bold cyan]Questions about your proof:[/bold cyan]\n")
        for i, question in enumerate(questions, 1):
            self.console.print(f"  {i}. {question}")
        self.console.print()

        # Collect answers
        self.console.print(
            "[dim]Please answer these questions to help me provide better feedback.\n"
            "You can answer briefly or skip with Enter.[/dim]\n"
        )

        answers = []
        for i, question in enumerate(questions, 1):
            self.console.print(f"[bold]Q{i}:[/bold] {question}")
            answer = Prompt.ask(f"[cyan]A{i}[/cyan]", default="")
            answers.append(answer)

            # Log the Q&A
            if self.logger and self.config.should_log_interactions():
                self.logger.log_user_input(f"question_{i}", answer)

            self.console.print()

        # Process answers and provide feedback
        self.console.print("[dim]Processing your answers...[/dim]\n")

        try:
            feedback_data = self.analyzer.process_answers(
                answers=answers,
                experience_level=experience_level,
                domain=domain,
            )
        except ValueError as e:
            self.console.print(f"[red]Failed to process answers:[/red] {e}")
            return

        # Display feedback
        self.console.print(Panel.fit(
            "[bold cyan]Proof Review Feedback[/bold cyan]",
            border_style="cyan",
        ))
        self.console.print()

        md = Markdown(feedback_data.get("feedback", "No feedback generated."))
        self.console.print(md)
        self.console.print()

    def _follow_up_loop(self) -> None:
        """Handle follow-up questions in a conversation loop."""
        self.console.print(
            "[dim]You can ask follow-up questions about the proof or feedback.\n"
            "Type 'quit' or 'exit' to end the session.[/dim]\n"
        )

        while True:
            try:
                user_input = Prompt.ask("[bold cyan]Follow-up[/bold cyan]", default="")

                if not user_input.strip():
                    if Confirm.ask("End the review session?", default=True):
                        self.console.print("[green]Thank you for the review session![/green]")
                        break
                    continue

                if user_input.lower() in ["quit", "exit", "q"]:
                    self.console.print("[green]Thank you for the review session![/green]")
                    break

                # Log the follow-up
                if self.logger and self.config.should_log_interactions():
                    self.logger.log_user_input("follow_up", user_input)

                # Continue the conversation
                self.console.print()
                response = self.analyzer.continue_conversation(user_input)

                md = Markdown(response)
                self.console.print(Panel(md, border_style="green"))
                self.console.print()

            except KeyboardInterrupt:
                self.console.print("\n[yellow]Session interrupted.[/yellow]")
                break


class ProofTeachingSession:
    """Manages an interactive proof teaching session using the Socratic method."""

    def __init__(self, config_manager: ConfigManager, console: Optional[Console] = None):
        """Initialize a proof teaching session.

        Args:
            config_manager: Configuration manager instance.
            console: Optional Rich console for formatted output.
        """
        self.config = config_manager
        self.console = console or Console()
        self.client = None
        self.model: str = ""
        self.conversation_history: List[Dict[str, str]] = []
        self.topic: str = ""
        self.domain: str = ""
        self.round_number: int = 0
        self.max_rounds: int = 5

        # Initialize logger if enabled
        self.logger: Optional[SessionLogger] = None
        if self.config.is_logging_enabled():
            self.logger = SessionLogger(
                config_dir=self.config.config_dir,
                enabled=True
            )

    def start_session(self, domain: Optional[str] = None) -> None:
        """Start an interactive proof teaching session.

        Args:
            domain: Optional mathematical domain to focus on.
        """
        import anthropic

        try:
            # Load configuration
            config = self.config.load()
            api_key = self.config.get_api_key()
            self.model = self.config.get_model()

            # Map experience level
            code_level = self.config.get("experience_level", "intermediate")
            level_map = {
                "beginner": "student",
                "intermediate": "undergrad",
                "advanced": "graduate",
                "expert": "researcher",
            }
            experience_level = level_map.get(code_level, "undergrad")

            # Initialize client
            self.client = anthropic.Anthropic(api_key=api_key)

            # Welcome message
            self._display_welcome()

            # Get domain if not provided
            if domain:
                self.domain = domain
            else:
                self.domain = self._get_domain()

            # Get topic
            self.topic = self._get_topic()

            # Start session logging
            if self.logger:
                self.logger.start_session("proof_teaching", {
                    "topic": self.topic,
                    "domain": self.domain,
                    "experience_level": experience_level,
                    "model": self.model,
                })

            # Run teaching rounds
            self._run_teaching_rounds(experience_level)

            # Conclusion
            self._display_conclusion()

            # End session logging
            if self.logger:
                self.logger.end_session()

        except ValueError as e:
            if self.logger:
                self.logger.log_error("ValueError", str(e))
            self.console.print(f"[red]Error:[/red] {e}")
        except KeyboardInterrupt:
            if self.logger:
                self.logger.end_session()
            self.console.print("\n\n[yellow]Teaching session interrupted. Goodbye![/yellow]")
        except Exception as e:
            if self.logger:
                import traceback
                self.logger.log_error("UnexpectedException", str(e), traceback.format_exc())
            self.console.print(f"[red]Unexpected error:[/red] {e}")

    def _display_welcome(self) -> None:
        """Display welcome message."""
        self.console.print(Panel.fit(
            "[bold cyan]Welcome to Proof Teaching Mode![/bold cyan]\n\n"
            "In this mode, I'll present proofs with subtle errors or gaps.\n"
            "Your task is to identify what's wrong and explain the issue.\n\n"
            "This Socratic approach helps you develop:\n"
            "  • Critical reading of mathematical arguments\n"
            "  • Understanding of common proof pitfalls\n"
            "  • Ability to spot logical gaps and errors\n\n"
            "Let's sharpen your proof-reading skills!",
            border_style="cyan",
            title="Proof Teaching"
        ))
        self.console.print()

    def _get_domain(self) -> str:
        """Get the mathematical domain to focus on.

        Returns:
            The domain string.
        """
        self.console.print("[bold]Which area of mathematics?[/bold]")
        self.console.print(
            "[dim]Examples: real analysis, linear algebra, abstract algebra, "
            "number theory, topology, combinatorics, logic[/dim]\n"
        )

        domain = Prompt.ask("Domain", default="real analysis")
        return domain

    def _get_topic(self) -> str:
        """Get the specific topic to practice.

        Returns:
            The topic string.
        """
        self.console.print(f"\n[bold]What topic in {self.domain} would you like to practice?[/bold]")
        self.console.print(
            "[dim]Examples: limits, continuity, group homomorphisms, "
            "induction, compactness, divisibility[/dim]\n"
        )

        topic = Prompt.ask("Topic")

        if self.logger and self.config.should_log_interactions():
            self.logger.log_user_input("topic_selection", topic)

        self.console.print(f"\n[green]Let's practice proofs about [bold]{topic}[/bold] in {self.domain}.[/green]\n")
        return topic

    def _run_teaching_rounds(self, experience_level: str) -> None:
        """Run the teaching rounds.

        Args:
            experience_level: User's experience level.
        """
        self.round_number = 0

        while self.round_number < self.max_rounds:
            self.round_number += 1

            self.console.print(f"\n[cyan]{'='*60}[/cyan]")
            self.console.print(f"[bold cyan]Round {self.round_number}[/bold cyan]")
            self.console.print(f"[cyan]{'='*60}[/cyan]\n")

            # Generate flawed proof
            proof_data = self._generate_flawed_proof(experience_level)

            if not proof_data:
                self.console.print("[yellow]Failed to generate proof. Ending session.[/yellow]")
                break

            # Display the proof
            self._display_proof(proof_data)

            # Get user's analysis
            analysis = self._get_user_analysis()

            if not analysis.strip():
                self.console.print("[yellow]Skipping this round...[/yellow]")
                continue

            # Evaluate the analysis
            evaluation = self._evaluate_analysis(
                proof_data["proof"],
                proof_data["issues"],
                analysis,
                experience_level,
            )

            # Display evaluation
            self._display_evaluation(evaluation)

            # Check if we should continue
            if evaluation.get("understanding_achieved", False):
                self.console.print(
                    "\n[green]Excellent analysis! You identified the key issues.[/green]"
                )

                if not Confirm.ask("\n[cyan]Try another flawed proof?[/cyan]", default=True):
                    break
            else:
                self.console.print(
                    "\n[yellow]There's more to find. Let's try another example...[/yellow]"
                )

    def _generate_flawed_proof(self, experience_level: str) -> Optional[Dict]:
        """Generate a proof with intentional flaws.

        Args:
            experience_level: User's experience level.

        Returns:
            Dictionary with proof and issues, or None if failed.
        """
        if self.round_number == 1:
            difficulty = "obvious but instructive"
        elif self.round_number <= 3:
            difficulty = "subtle"
        else:
            difficulty = "very subtle and requiring careful attention"

        prompt = f"""You are creating a teaching exercise about mathematical proofs.

Create a SHORT proof (5-15 lines) related to {self.topic} in {self.domain} that contains a {difficulty} error.

The error should be:
1. Instructive - teaches an important concept about proof writing
2. Realistic - a mistake a real student might make
3. Not trivial - requires thought to identify

For a {experience_level} level mathematician, adjust the sophistication accordingly.

Format your response as:

## Theorem
[State the theorem or claim being "proved"]

## Flawed Proof
[The proof with the intentional error(s)]

## Hidden Issues
[List what's actually wrong - for internal tracking only]
- Issue 1: [description]
- Issue 2: [if applicable]"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                messages=self.conversation_history + [{"role": "user", "content": prompt}],
            )

            content = response.content[0].text

            self.conversation_history.append({"role": "user", "content": prompt})
            self.conversation_history.append({"role": "assistant", "content": content})

            return self._parse_proof_response(content)

        except Exception as e:
            self.console.print(f"[red]Error generating proof:[/red] {e}")
            return None

    def _parse_proof_response(self, response: str) -> Dict:
        """Parse the proof generation response.

        Args:
            response: Raw response from Claude.

        Returns:
            Dictionary with theorem, proof, and issues.
        """
        lines = response.split("\n")
        theorem_lines = []
        proof_lines = []
        issues = []

        in_theorem = False
        in_proof = False
        in_issues = False

        for line in lines:
            if "## Theorem" in line:
                in_theorem = True
                in_proof = False
                in_issues = False
                continue
            elif "## Flawed Proof" in line or "## Proof" in line:
                in_theorem = False
                in_proof = True
                in_issues = False
                continue
            elif "## Hidden Issues" in line or "## Issues" in line:
                in_theorem = False
                in_proof = False
                in_issues = True
                continue
            elif line.startswith("##"):
                in_theorem = False
                in_proof = False
                in_issues = False
                continue

            if in_theorem and line.strip():
                theorem_lines.append(line)
            elif in_proof:
                proof_lines.append(line)
            elif in_issues and line.strip():
                cleaned = line.lstrip("*-•0123456789.) ").strip()
                if cleaned:
                    issues.append(cleaned)

        return {
            "theorem": "\n".join(theorem_lines).strip(),
            "proof": "\n".join(proof_lines).strip(),
            "issues": issues,
        }

    def _display_proof(self, proof_data: Dict) -> None:
        """Display the flawed proof.

        Args:
            proof_data: Dictionary with theorem and proof.
        """
        self.console.print(Panel.fit(
            f"[bold]Theorem:[/bold] {proof_data['theorem']}",
            border_style="yellow",
            title="Claim"
        ))
        self.console.print()

        self.console.print(Panel(
            proof_data["proof"],
            border_style="blue",
            title="Proof to Review"
        ))
        self.console.print()

    def _get_user_analysis(self) -> str:
        """Get the user's analysis of the flawed proof.

        Returns:
            The user's analysis.
        """
        self.console.print("[bold]What's wrong with this proof?[/bold]")
        self.console.print(
            "[dim]Identify any errors, gaps in reasoning, unjustified steps, "
            "or logical fallacies.[/dim]\n"
        )

        analysis = Prompt.ask("Your analysis")
        return analysis

    def _evaluate_analysis(
        self,
        proof: str,
        expected_issues: List[str],
        user_analysis: str,
        experience_level: str,
    ) -> Dict:
        """Evaluate the user's analysis.

        Args:
            proof: The flawed proof.
            expected_issues: List of issues in the proof.
            user_analysis: User's analysis.
            experience_level: User's experience level.

        Returns:
            Evaluation dictionary.
        """
        prompt = f"""Evaluate this student's analysis of a flawed proof.

The flawed proof:
{proof}

Known issues:
{chr(10).join(f"- {issue}" for issue in expected_issues)}

Student's analysis:
"{user_analysis}"

As a {experience_level} level student, evaluate:
1. Did they identify the main error(s)?
2. Is their explanation mathematically sound?
3. Did they explain WHY it's an error?

Respond with:

## Feedback
[Constructive feedback on their analysis. If they missed something, guide them toward it without giving it away entirely. If they got it, confirm and expand on the insight.]

## Understanding Achieved
[YES if they identified the key issue(s), NO if they need more guidance]"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=self.conversation_history + [{"role": "user", "content": prompt}],
            )

            content = response.content[0].text

            self.conversation_history.append({"role": "user", "content": prompt})
            self.conversation_history.append({"role": "assistant", "content": content})

            understanding = "YES" in content.upper() and "Understanding Achieved" in content

            return {
                "understanding_achieved": understanding,
                "feedback": content,
            }

        except Exception as e:
            self.console.print(f"[red]Error evaluating analysis:[/red] {e}")
            return {"understanding_achieved": False, "feedback": "Error occurred"}

    def _display_evaluation(self, evaluation: Dict) -> None:
        """Display the evaluation feedback.

        Args:
            evaluation: Evaluation dictionary.
        """
        self.console.print("\n[bold yellow]Feedback:[/bold yellow]\n")

        md = Markdown(evaluation.get("feedback", "No feedback available"))
        self.console.print(Panel(md, border_style="green", title="Evaluation"))

    def _display_conclusion(self) -> None:
        """Display conclusion message."""
        self.console.print(f"\n\n[bold green]Proof Teaching Session Complete![/bold green]")
        self.console.print(
            f"[dim]We completed {self.round_number} round(s) on: {self.topic} ({self.domain})[/dim]\n"
        )
        self.console.print(
            "[cyan]Remember: Spotting errors in proofs is a crucial skill.\n"
            "Keep practicing by critically reading proofs you encounter![/cyan]\n"
        )
