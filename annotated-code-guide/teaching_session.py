"""
Interactive teaching mode for learning through correcting mistakes.

📚 FILE OVERVIEW:
This file implements the "Teach Me!" mode where users learn by teaching.
The AI role-plays as a student with flawed code, and the user provides hints
and guidance. This Socratic method helps solidify understanding.

🎯 WHAT YOU'LL LEARN:
- Role-playing with AI (AI acts as student)
- Multi-round progressive difficulty
- Code generation with specific requirements
- Evaluation and feedback on teaching quality
- Complex prompt engineering for roleplay
- Conversation history across multiple rounds
- Syntax highlighting for code display

💡 WHY THIS FILE EXISTS:
Research shows that teaching others is one of the best ways to learn.
This mode lets users practice explaining concepts, which deepens their
own understanding. The AI provides a safe, judgment-free student to teach.
"""

# ============================================================================
# IMPORTS
# ============================================================================

from typing import Dict, List, Optional  # Type hints
import anthropic  # Claude API client

# Rich library for beautiful terminal output
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.syntax import Syntax  # 🎯 For syntax-highlighted code display!

# Our components
from .config import ConfigManager
from .logger import SessionLogger


# ============================================================================
# TeachingSession CLASS
# ============================================================================

class TeachingSession:
    """
    Manages an interactive teaching session using the Socratic method.

    🔍 DESIGN PATTERN: Role-Playing Orchestrator
    This is more complex than ReviewSession because:
    1. AI plays multiple roles (student asking questions, student responding)
    2. Multi-round progression with increasing difficulty
    3. Code generation (not just analysis)
    4. Teaching quality evaluation

    💡 KEY DIFFERENCES FROM REVIEW SESSION:
    - User is the teacher, AI is the student
    - AI generates flawed code for user to fix
    - Multi-round structure (up to 5 rounds)
    - Progressive difficulty scaling
    - Teaching hints evaluation

    🎯 WORKFLOW:
    1. Get topic from user (e.g., "recursion")
    2. Get language preference
    3. For each round (up to 5):
       a. Generate flawed code about topic
       b. Display code + student question
       c. Get user's teaching hints
       d. Evaluate hints (AI responds as student)
       e. Check if understanding achieved
       f. Continue or new problem
    4. Conclusion and encouragement
    """

    # ------------------------------------------------------------------------
    # INITIALIZATION
    # ------------------------------------------------------------------------

    def __init__(self, config_manager: ConfigManager, console: Optional[Console] = None):
        """
        Initialize a teaching session.

        💡 SIMILAR TO ReviewSession BUT:
        - Maintains its own Anthropic client (more direct API control)
        - Tracks round number and max rounds
        - Stores topic across rounds

        Args:
            config_manager: Configuration manager instance.
            console: Optional Rich console for formatted output.
        """
        self.config = config_manager
        self.console = console or Console()

        # API client (we manage this directly, not through analyzer)
        # 🔍 We create this in start_session() when we have the API key
        self.client: Optional[anthropic.Anthropic] = None
        self.model: str = ""  # Will be set from config

        # Conversation history across ALL rounds
        # 💡 This allows later rounds to build on earlier ones
        self.conversation_history: List[Dict[str, str]] = []

        # Session state
        self.topic: str = ""  # What concept are we teaching?
        self.round_number: int = 0  # Current round
        self.max_rounds: int = 5  # Maximum teaching rounds

        # Logger (optional)
        self.logger: Optional[SessionLogger] = None
        if self.config.is_logging_enabled():
            self.logger = SessionLogger(
                config_dir=self.config.config_dir,
                enabled=True
            )

    # ------------------------------------------------------------------------
    # MAIN WORKFLOW
    # ------------------------------------------------------------------------

    def start_session(self) -> None:
        """
        Start an interactive teaching session.

        🔍 MAIN ORCHESTRATION METHOD:
        Similar structure to ReviewSession.start_review() but:
        - Gets topic and language from user
        - Runs multiple teaching rounds
        - Doesn't analyze existing code (generates new code)

        Error Handling:
            - ValueError: API/configuration errors
            - KeyboardInterrupt: User pressed Ctrl+C
            - Exception: Unexpected errors
        """
        try:
            # ========================================
            # STEP 1: LOAD CONFIGURATION
            # ========================================

            config = self.config.load()
            api_key = self.config.get_api_key()
            self.model = self.config.get_model()
            experience_level = self.config.get("experience_level", "intermediate")

            # ========================================
            # STEP 2: INITIALIZE API CLIENT
            # ========================================

            self.client = anthropic.Anthropic(api_key=api_key)

            # ========================================
            # STEP 3: WELCOME AND SETUP
            # ========================================

            self._display_welcome()

            # Get what user wants to learn about
            self.topic = self._get_topic()

            # Get programming language preference
            language = self._get_language()

            # ========================================
            # STEP 4: START LOGGING
            # ========================================

            if self.logger:
                self.logger.start_session("teaching", {
                    "topic": self.topic,
                    "language": language,
                    "experience_level": experience_level,
                    "model": self.model,
                })

            # ========================================
            # STEP 5: RUN TEACHING ROUNDS
            # ========================================
            # 🎯 This is where the magic happens!

            self._run_teaching_rounds(experience_level, language)

            # ========================================
            # STEP 6: CONCLUSION
            # ========================================

            self._display_conclusion()

            # End logging
            if self.logger:
                self.logger.end_session()

        except ValueError as e:
            # Configuration or API error
            if self.logger:
                self.logger.log_error("ValueError", str(e))
            self.console.print(f"[red]Error:[/red] {e}")

        except KeyboardInterrupt:
            # User pressed Ctrl+C
            if self.logger:
                self.logger.end_session()
            self.console.print("\n\n[yellow]Teaching session interrupted. Goodbye![/yellow]")

        except Exception as e:
            # Unexpected error
            if self.logger:
                import traceback
                self.logger.log_error(
                    "UnexpectedException",
                    str(e),
                    traceback.format_exc()
                )
            self.console.print(f"[red]Unexpected error:[/red] {e}")

    # ------------------------------------------------------------------------
    # DISPLAY AND INPUT HELPERS
    # ------------------------------------------------------------------------

    def _display_welcome(self) -> None:
        """
        Display welcome message.

        💡 SETS EXPECTATIONS:
        - Explains the teaching mode concept
        - Clarifies user's role as teacher
        - Emphasizes hints over direct answers
        """
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
        """
        Get the topic the user wants to learn about.

        💡 EXAMPLES HELP:
        Providing examples guides users toward appropriate topics.

        Returns:
            The topic string (e.g., "recursion", "async/await").
        """
        self.console.print("[bold]What would you like to learn about?[/bold]")
        self.console.print(
            "[dim]Examples: recursion, async/await, design patterns, "
            "memory management, error handling[/dim]\n"
        )

        topic = Prompt.ask("Topic")

        # Log the selection
        if self.logger and self.config.should_log_interactions():
            self.logger.log_user_input("topic_selection", topic)

        self.console.print(
            f"\n[green]Great! Let's explore [bold]{topic}[/bold] together.[/green]\n"
        )

        return topic

    def _get_language(self) -> str:
        """
        Get the preferred programming language.

        💡 DEFAULT TO PYTHON:
        Python is beginner-friendly and widely used.

        Returns:
            The language string (e.g., "Python", "JavaScript").
        """
        self.console.print("[bold]Which programming language would you like to use?[/bold]")
        self.console.print("[dim]Examples: Python, JavaScript, Java, C++, Go, Rust[/dim]\n")

        language = Prompt.ask("Language", default="Python")

        # Log the selection
        if self.logger and self.config.should_log_interactions():
            self.logger.log_user_input("language_selection", language)

        return language

    # ------------------------------------------------------------------------
    # TEACHING ROUNDS
    # ------------------------------------------------------------------------

    def _run_teaching_rounds(self, experience_level: str, language: str) -> None:
        """
        Run the teaching rounds.

        🔍 MULTI-ROUND STRUCTURE:
        - Up to 5 rounds (self.max_rounds)
        - Each round: generate code → display → get hints → evaluate → check understanding
        - Conversation history maintained across rounds
        - Difficulty increases with round number

        💡 EXIT CONDITIONS:
        1. Reach max_rounds
        2. Code generation fails
        3. User declines to continue
        4. Understanding achieved and user doesn't want another problem

        Args:
            experience_level: User's experience level.
            language: Programming language to use.
        """
        self.round_number = 0  # Reset counter

        while self.round_number < self.max_rounds:
            self.round_number += 1

            # ========================================
            # DISPLAY ROUND HEADER
            # ========================================

            self.console.print(f"\n[cyan]{'='*60}[/cyan]")
            self.console.print(f"[bold cyan]Round {self.round_number}[/bold cyan]")
            self.console.print(f"[cyan]{'='*60}[/cyan]\n")

            # ========================================
            # GENERATE FLAWED CODE
            # ========================================
            # 🎯 AI creates code with intentional mistakes

            code_data = self._generate_flawed_code(experience_level, language)

            if not code_data:
                # Generation failed
                self.console.print(
                    "[yellow]Failed to generate code. Ending session.[/yellow]"
                )
                break

            # ========================================
            # DISPLAY CODE AND STUDENT QUESTION
            # ========================================

            self._display_code(
                code_data["code"],
                code_data.get("student_question", ""),
                language
            )

            # ========================================
            # GET USER'S TEACHING HINTS
            # ========================================

            explanation = self._get_user_explanation()

            if not explanation.strip():
                # Empty response - skip round
                self.console.print("[yellow]Skipping this round...[/yellow]")
                continue

            # ========================================
            # EVALUATE THE HINTS
            # ========================================
            # 💡 AI roleplays as student responding to hints

            evaluation = self._evaluate_explanation(
                code_data["code"],
                code_data["issues"],  # What's actually wrong
                explanation,  # User's teaching hints
                experience_level,
                language
            )

            # ========================================
            # DISPLAY EVALUATION
            # ========================================

            self._display_evaluation(evaluation)

            # ========================================
            # LOG THE ROUND
            # ========================================

            if self.logger and self.config.should_log_interactions():
                self.logger.log_teaching_round(
                    self.round_number,
                    self.topic,
                    language,
                    code_data["code"],
                    explanation,
                    evaluation.get("feedback", "")
                )

            # ========================================
            # CHECK IF CONTINUE
            # ========================================

            if evaluation.get("understanding_achieved", False):
                # Student understood! Good teaching!
                self.console.print(
                    "\n[green]Great teaching! The student has reached "
                    "understanding through your hints.[/green]"
                )

                # Ask if they want to help another "student"
                if not Confirm.ask(
                    "\n[cyan]Help another student with a new problem?[/cyan]",
                    default=True
                ):
                    break  # Exit loop

            else:
                # More guidance needed
                self.console.print(
                    "\n[yellow]The student needs more guidance. "
                    "Let's try another related example...[/yellow]"
                )
                # Continue to next round automatically

    # ------------------------------------------------------------------------
    # CODE GENERATION
    # ------------------------------------------------------------------------

    def _generate_flawed_code(self, experience_level: str, language: str) -> Optional[Dict]:
        """
        Generate code with intentional, instructive mistakes.

        🔍 THIS IS UNIQUE TO TEACHING MODE!
        Instead of analyzing existing code, we generate new code with
        specific, educational mistakes.

        💡 WHAT MAKES GOOD FLAWED CODE:
        1. Instructive - teaches an important concept
        2. Clever - not immediately obvious
        3. Realistic - something a real programmer might do
        4. Focused - ONE specific misconception

        Args:
            experience_level: User's experience level.
            language: Programming language.

        Returns:
            Dictionary with:
            {
                "code": "the flawed code",
                "student_question": "question from student perspective",
                "issues": ["issue 1", "issue 2"]
            }
            Or None if generation fails.
        """
        # Build the prompt for code generation
        prompt = self._build_code_generation_prompt(experience_level, language)

        try:
            # ========================================
            # API CALL
            # ========================================
            # 🔍 Note: We pass conversation_history + new prompt
            # This allows later rounds to build on earlier rounds

            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,  # Code generation needs fewer tokens
                messages=self.conversation_history + [{"role": "user", "content": prompt}],
            )

            content = response.content[0].text

            # ========================================
            # STORE IN CONVERSATION HISTORY
            # ========================================
            # 💡 Later rounds can reference earlier problems

            self.conversation_history.append({"role": "user", "content": prompt})
            self.conversation_history.append({"role": "assistant", "content": content})

            # ========================================
            # PARSE THE RESPONSE
            # ========================================

            return self._parse_code_response(content)

        except Exception as e:
            self.console.print(f"[red]Error generating code:[/red] {e}")
            return None

    def _build_code_generation_prompt(self, experience_level: str, language: str) -> str:
        """
        Build prompt for generating flawed code.

        🔍 PROGRESSIVE DIFFICULTY:
        - Round 1: Obvious but instructive
        - Rounds 2-3: Subtle and thought-provoking
        - Rounds 4-5: Nuanced, requiring deep understanding

        💡 PROMPT STRUCTURE:
        1. Role: "You are a student who needs help"
        2. Task: Create SHORT flawed code (5-15 lines)
        3. Requirements: Instructive, clever, realistic, focused
        4. Format: Exact output format with sections

        Args:
            experience_level: User's experience level.
            language: Programming language.

        Returns:
            The prompt string.
        """
        # ========================================
        # DETERMINE DIFFICULTY BASED ON ROUND
        # ========================================

        if self.round_number == 1:
            difficulty = "obvious but instructive"
        elif self.round_number <= 3:
            difficulty = "subtle and thought-provoking"
        else:
            difficulty = "nuanced and requiring deep understanding"

        # ========================================
        # BUILD THE PROMPT
        # ========================================
        # 🔍 Notice the specific format requirements
        # AI must follow this format for parsing to work

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
        """
        Parse the code generation response.

        🔍 STATE MACHINE PARSING:
        We track which section we're in:
        - in_code_block: Inside ```code``` fence
        - in_student_question: In "Student Question" section
        - in_issues: In "Hidden Issues" section

        💡 PARSING CHALLENGES:
        - Code blocks use ``` markers
        - Sections start with ## headers
        - Need to extract and clean text

        Args:
            response: Raw response from Claude.

        Returns:
            Dictionary with code, student_question, and issues.
        """
        lines = response.split("\n")

        # Storage for extracted parts
        code_lines = []
        student_question_lines = []
        issues = []

        # State machine flags
        in_code_block = False
        in_student_question = False
        in_issues = False

        # ========================================
        # PARSE LINE BY LINE
        # ========================================

        for line in lines:
            # Check for code block markers
            if "```" in line:
                in_code_block = not in_code_block  # Toggle
                continue  # Don't include ``` in output

            # Check for section headers
            if "## Student Question" in line:
                in_student_question = True
                in_issues = False
                continue

            elif "## Hidden Issues" in line or "## Issues" in line:
                in_issues = True
                in_student_question = False
                continue

            elif line.startswith("##"):
                # Different section - reset flags
                in_student_question = False
                if in_issues:
                    in_issues = False

            # ========================================
            # EXTRACT CONTENT BASED ON STATE
            # ========================================

            if in_code_block:
                # Inside code block
                code_lines.append(line)

            elif in_student_question and line.strip():
                # Student question text
                student_question_lines.append(line.strip())

            elif in_issues and line.strip():
                # Issue list item - remove bullet points
                cleaned = line.lstrip("*-•").strip()
                if cleaned:
                    issues.append(cleaned)

        # ========================================
        # RETURN PARSED DATA
        # ========================================

        return {
            "code": "\n".join(code_lines),
            "student_question": " ".join(student_question_lines),  # Join into paragraph
            "issues": issues  # List of issues
        }

    # ------------------------------------------------------------------------
    # DISPLAY CODE
    # ------------------------------------------------------------------------

    def _display_code(self, code: str, student_question: str, language: str) -> None:
        """
        Display code with syntax highlighting and student's question.

        🔍 SYNTAX HIGHLIGHTING:
        Rich's Syntax class provides beautiful code highlighting with:
        - Language-specific coloring
        - Line numbers
        - Themed appearance

        💡 PRESENTATION:
        - Student question in a "speech bubble" panel
        - Code in a separate panel with syntax highlighting
        - Visual separation for clarity

        Args:
            code: Code to display.
            student_question: The student's question about the code.
            language: Programming language.
        """
        # ========================================
        # DISPLAY STUDENT'S QUESTION
        # ========================================

        self.console.print(Panel.fit(
            f"[italic]{student_question}[/italic]",
            border_style="yellow",
            title="🧑‍💻 Student Question",
            subtitle="(What hints can you give?)"
        ))
        self.console.print()

        # ========================================
        # DISPLAY CODE WITH SYNTAX HIGHLIGHTING
        # ========================================
        # 🎯 Syntax() creates a syntax-highlighted renderable

        syntax = Syntax(
            code,
            language.lower(),  # Language for highlighting
            theme="monokai",  # Color theme
            line_numbers=True  # Show line numbers
        )

        self.console.print(Panel(
            syntax,
            border_style="blue",
            title="Student's Code"
        ))
        self.console.print()

    def _get_user_explanation(self) -> str:
        """
        Get the user's teaching response with hints.

        💡 GUIDANCE:
        Remind user to give hints, not answers.
        This is the heart of Socratic teaching.

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

    # ------------------------------------------------------------------------
    # EVALUATION
    # ------------------------------------------------------------------------

    def _evaluate_explanation(
        self,
        code: str,
        expected_issues: List[str],
        user_explanation: str,
        experience_level: str,
        language: str
    ) -> Dict:
        """
        Evaluate the user's explanation.

        🔍 ROLEPLAY EVALUATION:
        AI now switches roles:
        - Before: AI was student asking for help
        - Now: AI evaluates teaching hints and responds as student

        💡 WHAT WE EVALUATE:
        1. Did they give hints without revealing the answer?
        2. Were hints specific enough to guide toward solution?
        3. Did they ask good guiding questions?
        4. Balance between helpful and letting student learn?

        Args:
            code: The flawed code.
            expected_issues: List of issues in the code.
            user_explanation: User's explanation.
            experience_level: User's experience level.
            language: Programming language.

        Returns:
            Evaluation dictionary with:
            {
                "understanding_achieved": True/False,
                "feedback": "full evaluation text"
            }
        """
        # ========================================
        # BUILD EVALUATION PROMPT
        # ========================================
        # 🔍 chr(10) is newline character for formatting

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
            # ========================================
            # API CALL FOR EVALUATION
            # ========================================

            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,  # Shorter response for evaluation
                messages=self.conversation_history + [{"role": "user", "content": prompt}],
            )

            content = response.content[0].text

            # ========================================
            # STORE IN HISTORY
            # ========================================
            # 💡 This evaluation becomes part of the teaching narrative

            self.conversation_history.append({"role": "user", "content": prompt})
            self.conversation_history.append({"role": "assistant", "content": content})

            return self._parse_evaluation_response(content)

        except Exception as e:
            self.console.print(f"[red]Error evaluating explanation:[/red] {e}")
            return {"understanding_achieved": False, "feedback": "Error occurred"}

    def _parse_evaluation_response(self, response: str) -> Dict:
        """
        Parse the evaluation response.

        🔍 SIMPLE PARSING:
        We just look for "YES" in the "Understanding Achieved" section.

        💡 COULD BE ENHANCED:
        Parse the three sections separately:
        - Student Response
        - Teaching Quality Assessment
        - Understanding Achieved

        Args:
            response: Raw response from Claude.

        Returns:
            Dictionary with evaluation data.
        """
        # Simple check: Does response contain "YES" near "Understanding Achieved"?
        understanding_achieved = (
            "YES" in response.upper() and
            "Understanding Achieved" in response
        )

        return {
            "understanding_achieved": understanding_achieved,
            "feedback": response  # Full response
        }

    def _display_evaluation(self, evaluation: Dict) -> None:
        """
        Display the evaluation feedback.

        💡 STUDENT'S RESPONSE:
        Shows how the "student" (AI) reacted to the teaching hints.

        Args:
            evaluation: Evaluation dictionary.
        """
        self.console.print("\n[bold yellow]Student's Response:[/bold yellow]\n")

        md = Markdown(evaluation.get("feedback", "No feedback available"))
        self.console.print(Panel(
            md,
            border_style="green",
            title="🧑‍💻 After Your Hints"
        ))

    def _display_conclusion(self) -> None:
        """
        Display conclusion message.

        💡 ENCOURAGEMENT:
        Reinforce the value of teaching as a learning method.
        """
        self.console.print(f"\n\n[bold green]Teaching Session Complete![/bold green]")
        self.console.print(
            f"[dim]We completed {self.round_number} round(s) on the topic: {self.topic}[/dim]\n"
        )
        self.console.print(
            "[cyan]Remember: Teaching others is one of the best ways to learn!\n"
            "Keep practicing by explaining concepts to yourself and others.[/cyan]\n"
        )


# ============================================================================
# KEY TAKEAWAYS
# ============================================================================
"""
🎓 WHAT YOU LEARNED:

1. **Role-Playing with AI**
   - AI can play different roles (student, evaluator)
   - Maintain consistent character through prompts
   - Evaluate user's teaching effectiveness

2. **Progressive Difficulty**
   - Scale difficulty based on round number
   - Start easy, build confidence, then challenge
   - if-elif-else for difficulty selection

3. **Multi-Round State Management**
   - Track round number
   - Maintain conversation history across rounds
   - Each round builds on previous ones

4. **Code Generation vs. Analysis**
   - Generate code with specific requirements
   - Different from analyzing existing code
   - Requires precise prompt formatting

5. **Complex Prompt Engineering**
   - Role assignment with context
   - Specific format requirements (##Code, ##Question, ##Issues)
   - Evaluation criteria in prompts

6. **State Machine Parsing**
   - Track parsing state with boolean flags
   - Switch states based on markers (##, ```)
   - Extract content based on current state

7. **Syntax Highlighting**
   - Syntax() from Rich library
   - Language-specific coloring
   - Line numbers for reference

8. **Socratic Method Implementation**
   - Don't give answers, give hints
   - Ask guiding questions
   - Evaluate teaching quality
   - Promote discovery learning

🔧 PATTERNS USED:

**Pattern: Progressive Difficulty**
```python
if round_number == 1:
    difficulty = "easy"
elif round_number <= 3:
    difficulty = "medium"
else:
    difficulty = "hard"
```

**Pattern: State Machine Parser**
```python
state = None
for line in lines:
    if marker_for_state_A in line:
        state = "A"
    elif state == "A":
        process_as_A(line)
```

**Pattern: Multi-Round Conversation**
```python
history = []
for round in range(max_rounds):
    prompt = build_prompt(round)
    history.append({"role": "user", "content": prompt})
    response = api_call(history)  # Uses full history!
    history.append({"role": "assistant", "content": response})
```

**Pattern: Role-Playing Prompts**
```python
prompt = f"""You are roleplaying as {role}.
Your character: {character_traits}
Your task: {task}
Respond as the character would."""
```

📚 FURTHER LEARNING:
- Socratic method pedagogy
- Role-playing with AI
- Progressive difficulty design
- Teaching effectiveness evaluation
- Multi-turn conversation design
- State machine parsing patterns
"""
