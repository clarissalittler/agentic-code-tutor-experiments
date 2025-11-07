"""
Interactive code review session management.

📚 FILE OVERVIEW:
This file orchestrates the complete code review workflow from start to finish.
It brings together all the core components (config, file_reader, analyzer, logger)
and manages the user interaction flow.

🎯 WHAT YOU'LL LEARN:
- Orchestration pattern (coordinating multiple components)
- Interactive CLI workflows with user prompts
- Error handling across a complex process
- Rich library for beautiful terminal output
- State management during a session
- Dependency injection pattern

💡 WHY THIS FILE EXISTS:
The core files provide building blocks (read files, call API, log events).
This file is the "instruction manual" that combines them into a complete
user experience.
"""

# ============================================================================
# IMPORTS
# ============================================================================

# 💡 Type hints for documentation
from typing import Dict, List, Optional

# 🔍 Rich library - Beautiful terminal formatting
from rich.console import Console  # Main console for output
from rich.markdown import Markdown  # Render markdown text
from rich.panel import Panel  # Create bordered panels
from rich.prompt import Prompt, Confirm  # Interactive user prompts

# 🎯 Our core components (built in previous files)
from .analyzer import CodeAnalyzer  # Claude API integration
from .config import ConfigManager  # Configuration management
from .file_reader import FileReader  # File I/O utilities
from .logger import SessionLogger  # Event logging


# ============================================================================
# ReviewSession CLASS
# ============================================================================

class ReviewSession:
    """
    Manages an interactive code review session.

    🔍 DESIGN PATTERN: Orchestrator/Coordinator
    This class doesn't do the heavy lifting itself. Instead, it:
    1. Coordinates multiple specialized components
    2. Manages the workflow sequence
    3. Handles user interaction
    4. Formats output for display

    💡 KEY RESPONSIBILITIES:
    - Load configuration
    - Read source files
    - Orchestrate API calls through analyzer
    - Display results beautifully
    - Handle errors gracefully
    - Log everything (if enabled)

    🎯 WORKFLOW:
    1. Initialize components
    2. Read file
    3. Analyze code (get questions + observations)
    4. Display observations
    5. Ask questions, collect answers
    6. Generate feedback
    7. Display feedback
    8. Allow follow-up dialogue
    9. Clean up and log
    """

    # ------------------------------------------------------------------------
    # INITIALIZATION
    # ------------------------------------------------------------------------

    def __init__(self, config_manager: ConfigManager, console: Optional[Console] = None):
        """
        Initialize a review session.

        🔍 DEPENDENCY INJECTION PATTERN:
        Instead of creating ConfigManager here, we receive it as a parameter.
        This makes testing easier and follows the principle: "Don't create
        what you can inject."

        💡 WHY OPTIONAL CONSOLE:
        - Allows tests to inject a custom console
        - Allows CLI to share one console across multiple sessions
        - Provides default for simple usage

        Args:
            config_manager: Configuration manager instance (injected).
            console: Optional Rich console for formatted output (injected or created).
        """
        # Store injected config manager
        self.config = config_manager

        # Use provided console or create new one
        # 🎯 Pattern: "or" operator for defaults
        self.console = console or Console()

        # Create file reader
        # 💡 FileReader has no state, so we create it here
        self.file_reader = FileReader()

        # Analyzer will be created later (needs API key from config)
        # ⚠️ Type hint shows it can be None initially
        self.analyzer: Optional[CodeAnalyzer] = None

        # ========================================
        # CONDITIONAL LOGGER INITIALIZATION
        # ========================================
        # 🔍 Only create logger if enabled in config

        self.logger: Optional[SessionLogger] = None

        # Check if logging is enabled
        if self.config.is_logging_enabled():
            # Create logger with same config directory
            self.logger = SessionLogger(
                config_dir=self.config.config_dir,
                enabled=True
            )

    # ------------------------------------------------------------------------
    # MAIN WORKFLOW METHOD
    # ------------------------------------------------------------------------

    def start_review(self, file_path: str) -> None:
        """
        Start an interactive code review session.

        🔍 THIS IS THE MAIN ORCHESTRATION METHOD!
        This method runs the complete workflow from start to finish.

        💡 ERROR HANDLING STRATEGY:
        - Try block wraps entire workflow
        - Specific exceptions caught first (FileNotFoundError, ValueError)
        - Generic Exception as last resort
        - All errors logged (if logging enabled)
        - User-friendly error messages displayed

        Args:
            file_path: Path to the file to review.

        Workflow Steps:
            1. Load config and initialize components
            2. Read and validate file
            3. Analyze code with Claude
            4. Display observations
            5. Ask questions and collect answers
            6. Generate personalized feedback
            7. Display feedback
            8. Allow follow-up dialogue
            9. Log session end
        """
        try:
            # ========================================
            # STEP 1: LOAD CONFIGURATION
            # ========================================
            # 🔍 Get all settings needed for the session

            config = self.config.load()  # Load from disk
            api_key = self.config.get_api_key()  # Raises error if not set
            model = self.config.get_model()  # Which Claude model to use
            experience_level = self.config.get("experience_level", "intermediate")
            preferences = self.config.get("preferences", {})

            # ========================================
            # STEP 2: START SESSION LOGGING
            # ========================================
            # 💡 Log metadata about this session

            if self.logger:
                self.logger.start_session("review", {
                    "file_path": file_path,
                    "experience_level": experience_level,
                    "preferences": preferences,
                    "model": model,
                })

            # ========================================
            # STEP 3: INITIALIZE ANALYZER
            # ========================================
            # 🎯 Now that we have API key, create analyzer

            self.analyzer = CodeAnalyzer(api_key, model)

            # ========================================
            # STEP 4: READ THE FILE
            # ========================================

            # Display progress message
            self.console.print(f"\n[cyan]Reading file:[/cyan] {file_path}")

            # Read file content + metadata
            file_data = self.file_reader.read_file(file_path)

            # Extract metadata for display
            metadata = file_data["metadata"]

            # Show file info to user
            # 🔍 [dim] makes text less prominent (secondary info)
            self.console.print(
                f"[dim]Language: {metadata['language']} | "
                f"Lines: {metadata['line_count']} | "
                f"Size: {metadata['size_bytes']} bytes[/dim]\n"
            )

            # ========================================
            # STEP 5: ANALYZE CODE
            # ========================================

            self.console.print("[cyan]Analyzing code...[/cyan]")

            # Call analyzer (makes API call to Claude)
            analysis = self.analyzer.analyze_code(
                file_data["content"],  # The actual code
                metadata,  # File metadata
                experience_level,  # User's skill level
                preferences,  # User preferences
            )

            # Log the analysis
            if self.logger and self.config.should_log_interactions():
                self.logger.log_code_analysis(
                    file_path,
                    file_data["content"],
                    str(analysis)  # Convert dict to string for logging
                )

            # ========================================
            # STEP 6: DISPLAY OBSERVATIONS
            # ========================================
            # 💡 Show initial impressions before asking questions

            if analysis.get("observations"):
                # Helper method handles Rich formatting
                self._display_observations(analysis["observations"])

                # Log observations
                if self.logger and self.config.should_log_interactions():
                    self.logger.log_ai_response(
                        "observations",
                        "\n".join(analysis["observations"]),
                        {"file_path": file_path}
                    )

            # ========================================
            # STEP 7: ASK QUESTIONS
            # ========================================

            questions = analysis.get("questions", [])

            if questions:
                # Collect user's answers
                # 🎯 Helper method handles prompting and logging
                answers = self._ask_questions(questions)

                # ========================================
                # STEP 8: GENERATE FEEDBACK
                # ========================================

                self.console.print("\n[cyan]Generating personalized feedback...[/cyan]\n")

                # Process answers (second API call with conversation history)
                feedback_data = self.analyzer.process_answers(
                    answers,
                    experience_level,
                    preferences
                )

                # ========================================
                # STEP 9: DISPLAY FEEDBACK
                # ========================================

                self._display_feedback(feedback_data["feedback"])

                # ========================================
                # STEP 10: FOLLOW-UP CONVERSATION
                # ========================================
                # 💡 Optional Q&A loop

                self._follow_up_conversation()

            else:
                # ⚠️ No questions generated - might indicate API issue
                self.console.print(
                    "[yellow]No questions generated. This might indicate an issue.[/yellow]"
                )

            # ========================================
            # STEP 11: END SESSION
            # ========================================

            if self.logger:
                self.logger.end_session()

        # ========================================
        # ERROR HANDLING
        # ========================================
        # 🔍 Catch specific errors with appropriate messages

        except FileNotFoundError as e:
            # File doesn't exist
            if self.logger:
                self.logger.log_error("FileNotFoundError", str(e))
            self.console.print(f"[red]Error:[/red] {e}")

        except ValueError as e:
            # Configuration issue, API error, or validation error
            if self.logger:
                self.logger.log_error("ValueError", str(e))
            self.console.print(f"[red]Error:[/red] {e}")

        except Exception as e:
            # Unexpected error - catch all
            if self.logger:
                import traceback
                # Log full traceback for debugging
                self.logger.log_error(
                    "UnexpectedException",
                    str(e),
                    traceback.format_exc()
                )
            self.console.print(f"[red]Unexpected error:[/red] {e}")

    # ------------------------------------------------------------------------
    # DISPLAY HELPERS
    # ------------------------------------------------------------------------
    # 💡 These methods handle Rich formatting for different output types

    def _display_observations(self, observations: List[str]) -> None:
        """
        Display initial observations.

        🔍 RICH PANEL:
        Panel.fit() creates a bordered box that auto-sizes to content.

        💡 FORMATTING:
        - [bold] for title
        - • bullets for list items
        - border_style="blue" for colored border

        Args:
            observations: List of observation strings.
        """
        # Build the panel content
        # 🎯 f"• {obs}" adds bullet point to each observation
        content = "[bold]Initial Observations[/bold]\n\n" + \
                  "\n".join(f"• {obs}" for obs in observations)

        # Display in a blue-bordered panel
        self.console.print(Panel.fit(
            content,
            border_style="blue",
        ))
        self.console.print()  # Extra newline for spacing

    def _ask_questions(self, questions: List[str]) -> List[str]:
        """
        Ask the user questions and collect answers.

        🔍 INTERACTIVE PROMPTING:
        Uses Rich's Prompt.ask() for user input with nice formatting.

        💡 LOGGING PATTERN:
        - Log each question before asking
        - Log each answer after receiving
        - Include context (question number, total questions)

        Args:
            questions: List of questions to ask.

        Returns:
            List of user's answers (same length as questions).
        """
        # Display header panel
        self.console.print(Panel.fit(
            "[bold]I have some questions about your code[/bold]\n\n" +
            "Please help me understand your design decisions:",
            border_style="cyan",
        ))
        self.console.print()

        answers = []

        # Loop through questions (enumerate starts at 1 for display)
        for i, question in enumerate(questions, 1):
            # ========================================
            # LOG THE QUESTION
            # ========================================

            if self.logger and self.config.should_log_interactions():
                self.logger.log_ai_response(
                    "question",
                    question,
                    {"question_number": i, "total_questions": len(questions)}
                )

            # ========================================
            # DISPLAY AND PROMPT
            # ========================================

            # Display question with number
            self.console.print(f"[bold cyan]Question {i}:[/bold cyan] {question}\n")

            # Get user's answer
            # 🎯 [dim] makes the prompt text less prominent
            answer = Prompt.ask("[dim]Your answer[/dim]")

            answers.append(answer)

            # ========================================
            # LOG THE ANSWER
            # ========================================

            if self.logger and self.config.should_log_interactions():
                self.logger.log_user_input(
                    "answer",
                    answer,
                    {"question": question, "question_number": i}
                )

            self.console.print()  # Spacing

        return answers

    def _display_feedback(self, feedback: str) -> None:
        """
        Display feedback using rich formatting.

        🔍 MARKDOWN RENDERING:
        Rich can render markdown text with proper formatting:
        - **bold** → bold text
        - # Headers → styled headers
        - - Lists → formatted lists
        - `code` → syntax highlighting

        Args:
            feedback: Feedback text (markdown formatted from Claude).
        """
        # Log before displaying
        if self.logger and self.config.should_log_interactions():
            self.logger.log_ai_response("feedback", feedback)

        # Display header
        self.console.print(Panel.fit(
            "[bold green]Feedback & Suggestions[/bold green]",
            border_style="green",
        ))
        self.console.print()

        # Render markdown
        # 💡 Markdown() converts markdown text to Rich renderable
        md = Markdown(feedback)
        self.console.print(md)
        self.console.print()

    # ------------------------------------------------------------------------
    # FOLLOW-UP CONVERSATION
    # ------------------------------------------------------------------------

    def _follow_up_conversation(self) -> None:
        """
        Allow user to ask follow-up questions.

        🔍 INFINITE LOOP PATTERN:
        - while True loop
        - Break when user says no to follow-up
        - Ctrl+C (KeyboardInterrupt) exits gracefully

        💡 CONVERSATION CONTINUITY:
        Uses analyzer.continue_conversation() which maintains
        full conversation history for context.
        """
        self.console.print(
            "[dim]You can now ask follow-up questions, or press Ctrl+C to exit.[/dim]\n"
        )

        try:
            while True:  # Loop until user wants to exit
                # ========================================
                # ASK IF USER WANTS TO CONTINUE
                # ========================================
                # 🎯 Confirm.ask() returns True/False

                wants_followup = Confirm.ask(
                    "[cyan]Do you have any follow-up questions?[/cyan]",
                    default=False,  # Default to "no" (safer choice)
                )

                if not wants_followup:
                    # User is done
                    self.console.print(
                        "\n[green]Review session complete! Happy coding! 🎉[/green]"
                    )
                    break  # Exit the loop

                # ========================================
                # GET USER'S QUESTION
                # ========================================

                question = Prompt.ask("\n[bold]Your question[/bold]")

                # Skip if empty
                if not question.strip():
                    continue  # Go back to start of loop

                # Log the question
                if self.logger and self.config.should_log_interactions():
                    self.logger.log_user_input(
                        "question",
                        question,
                        {"type": "follow_up"}
                    )

                # ========================================
                # GET AI RESPONSE
                # ========================================

                self.console.print("\n[cyan]Thinking...[/cyan]\n")

                # Continue conversation (uses full history)
                response = self.analyzer.continue_conversation(question)

                # Log the response
                if self.logger and self.config.should_log_interactions():
                    self.logger.log_ai_response(
                        "answer",
                        response,
                        {"type": "follow_up"}
                    )

                # ========================================
                # DISPLAY RESPONSE
                # ========================================

                md = Markdown(response)
                self.console.print(Panel(md, border_style="blue"))
                self.console.print()

        except KeyboardInterrupt:
            # ⚠️ User pressed Ctrl+C
            # Handle gracefully instead of crashing
            self.console.print("\n\n[yellow]Session interrupted. Goodbye![/yellow]")

    # ------------------------------------------------------------------------
    # DIRECTORY REVIEW
    # ------------------------------------------------------------------------

    def review_directory(self, directory: str, recursive: bool = True) -> None:
        """
        Review multiple files in a directory.

        🔍 EXTENDS SINGLE FILE REVIEW:
        - Finds all supported files
        - Lets user select which to review
        - Reviews each file sequentially
        - Resets conversation between files

        💡 USER CHOICE PATTERN:
        - Show list of files
        - Ask if review all
        - If no, let user select specific files
        - Validate selection

        Args:
            directory: Directory path to review.
            recursive: Whether to search recursively (default: True).
        """
        try:
            # ========================================
            # FIND FILES
            # ========================================

            files = self.file_reader.find_files(directory, recursive)

            if not files:
                self.console.print(
                    f"[yellow]No supported source files found in {directory}[/yellow]"
                )
                return  # Exit early

            # ========================================
            # DISPLAY FILE LIST
            # ========================================

            self.console.print(f"\n[cyan]Found {len(files)} file(s) to review:[/cyan]")
            for i, file in enumerate(files, 1):
                self.console.print(f"  {i}. {file}")

            self.console.print()

            # ========================================
            # GET USER SELECTION
            # ========================================

            # Ask if review all files
            proceed = Confirm.ask("Review all files?", default=False)

            if not proceed:
                # User wants to select specific files
                selection = Prompt.ask(
                    "Enter file numbers to review (comma-separated) or 'all'",
                    default="all"
                )

                if selection.lower() != "all":
                    # Parse selection
                    try:
                        # Split by comma, convert to int, subtract 1 for 0-indexing
                        indices = [int(x.strip()) - 1 for x in selection.split(",")]

                        # Filter files by selected indices
                        # 🔍 List comprehension with bounds checking
                        files = [files[i] for i in indices if 0 <= i < len(files)]

                    except (ValueError, IndexError):
                        # Invalid input
                        self.console.print("[red]Invalid selection[/red]")
                        return

            # ========================================
            # REVIEW EACH FILE
            # ========================================

            for i, file in enumerate(files, 1):
                # Display separator
                self.console.print(f"\n[bold cyan]{'='*60}[/bold cyan]")
                self.console.print(f"[bold cyan]Reviewing file {i}/{len(files)}[/bold cyan]")
                self.console.print(f"[bold cyan]{'='*60}[/bold cyan]")

                # Review this file
                # 🎯 Reuses start_review() - code reuse!
                self.start_review(file)

                # Ask if continue to next file (except for last file)
                if i < len(files):
                    self.console.print()
                    if not Confirm.ask("Continue to next file?", default=True):
                        break  # User wants to stop

                # ========================================
                # RESET CONVERSATION
                # ========================================
                # 💡 Clear history so next file starts fresh

                if self.analyzer:
                    self.analyzer.reset_conversation()

        except Exception as e:
            self.console.print(f"[red]Error:[/red] {e}")


# ============================================================================
# KEY TAKEAWAYS
# ============================================================================
"""
🎓 WHAT YOU LEARNED:

1. **Orchestration Pattern**
   - Coordinator class that uses specialized components
   - Each component does one thing well
   - Orchestrator manages workflow and timing

2. **Dependency Injection**
   - Pass dependencies as parameters, don't create them
   - Makes testing easier
   - Allows flexibility (different console, config, etc.)

3. **Rich Library Integration**
   - Console() for output
   - Panel() for bordered boxes
   - Markdown() for formatted text
   - Prompt.ask() and Confirm.ask() for input
   - [color] syntax for styling

4. **Error Handling Hierarchy**
   - Specific exceptions first
   - Generic Exception last
   - Log all errors
   - Display user-friendly messages

5. **Interactive Workflows**
   - while True loop for ongoing interaction
   - Confirm.ask() for yes/no questions
   - Prompt.ask() for text input
   - KeyboardInterrupt for graceful Ctrl+C handling

6. **Conditional Logging**
   - Check if enabled before logging
   - Log key events (start, end, input, output)
   - Include context with each log entry

7. **Helper Methods**
   - _display_observations()
   - _ask_questions()
   - _display_feedback()
   - _follow_up_conversation()
   - Each handles one UI responsibility

🔧 PATTERNS USED:

**Pattern: Orchestrator/Coordinator**
```python
class Orchestrator:
    def __init__(self):
        self.component1 = Component1()
        self.component2 = Component2()

    def do_workflow(self):
        data = self.component1.step1()
        result = self.component2.step2(data)
        return result
```

**Pattern: Try-Except with Multiple Handlers**
```python
try:
    do_work()
except SpecificError1 as e:
    handle_specific1(e)
except SpecificError2 as e:
    handle_specific2(e)
except Exception as e:
    handle_generic(e)
```

**Pattern: Interactive Loop**
```python
try:
    while True:
        if not Confirm.ask("Continue?"):
            break
        process_user_input()
except KeyboardInterrupt:
    cleanup_and_exit()
```

📚 FURTHER LEARNING:
- Rich library documentation
- Click framework for CLI
- Orchestration vs. implementation
- Dependency injection patterns
- Interactive terminal UI design
- Error handling best practices
"""
