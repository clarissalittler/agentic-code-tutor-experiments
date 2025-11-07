# Orchestration Files - session.py, teaching_session.py, cli.py

These three files bring together all the components you learned about in the core files. Instead of duplicating hundreds of lines of code, this guide explains the key concepts and patterns used.

## Why These Files Are Different

The four core files (config.py, file_reader.py, analyzer.py, logger.py) are **building blocks** - they each do one thing well.

These three files are **orchestrators** - they combine the building blocks to create complete workflows.

Think of it like this:
- Core files = LEGO bricks
- Orchestration files = LEGO instruction manual (how to combine the bricks)

---

## session.py - Code Review Workflow

### Purpose
Orchestrates the complete code review experience from start to finish.

### Key Concepts

#### 1. Session Class Pattern
```python
class ReviewSession:
    def __init__(self, config_manager, console):
        # Initialize all the components
        self.config = config_manager
        self.console = console
        self.file_reader = FileReader()
        self.analyzer = None  # Created later
        self.logger = None    # Optional
```

**🔍 Why this works**: All dependencies are injected, making testing easier.

#### 2. The Main Workflow: `start_review()`

```
start_review(file_path):
│
├─ 1. Load config and initialize components
│   ├─ Get API key, model, experience level
│   └─ Create CodeAnalyzer with config
│
├─ 2. Read the file
│   ├─ FileReader.read_file(path)
│   └─ Display file metadata
│
├─ 3. Analyze code
│   ├─ analyzer.analyze_code(...)
│   └─ Returns questions + observations
│
├─ 4. Display observations
│   └─ Rich Panel with bullet points
│
├─ 5. Ask questions
│   ├─ Display each question in Rich panel
│   ├─ Prompt.ask() for each answer
│   └─ Log each Q&A pair
│
├─ 6. Generate feedback
│   ├─ analyzer.process_answers(...)
│   └─ Returns personalized feedback
│
├─ 7. Display feedback
│   └─ Rich Markdown rendering
│
└─ 8. Follow-up loop
    ├─ Offer to continue conversation
    ├─ If yes: continue_conversation()
    ├─ If no: end session
    └─ Repeat until user exits
```

#### 3. Rich Library Integration

**Panels for Structure**:
```python
from rich.panel import Panel

self.console.print(Panel.fit(
    "[bold]Initial Observations[/bold]\n\n" +
    "\n".join(f"• {obs}" for obs in observations),
    border_style="blue",
))
```

**Markdown for Feedback**:
```python
from rich.markdown import Markdown

md = Markdown(feedback_text)
self.console.print(md)
```

**Prompts for Input**:
```python
from rich.prompt import Prompt, Confirm

answer = Prompt.ask("Your answer")
continue_session = Confirm.ask("Continue?", default=False)
```

#### 4. Error Handling Pattern

```python
try:
    # Try to perform operation
    result = do_something()

except FileNotFoundError as e:
    # Log specific error
    if self.logger:
        self.logger.log_error("FileNotFoundError", str(e))
    # Display user-friendly message
    self.console.print(f"[red]Error:[/red] {e}")

except Exception as e:
    # Catch-all for unexpected errors
    if self.logger:
        import traceback
        self.logger.log_error("UnexpectedException", str(e), traceback.format_exc())
    self.console.print(f"[red]Unexpected error:[/red] {e}")
```

**🎯 Pattern**: Specific exceptions first, then general Exception catch-all.

#### 5. Directory Review

The `review_directory()` method adds:
- Finding all supported files
- Showing file list
- Letting user select files
- Reviewing each file in sequence
- Resetting analyzer between files

---

## teaching_session.py - Socratic Teaching Mode

### Purpose
Implements "Teach Me!" mode where the user acts as teacher.

### Unique Challenge

Unlike review mode (analyze existing code), teaching mode must:
1. **Generate** flawed code
2. **Roleplay** as a student
3. **Evaluate** the user's teaching hints
4. **Adapt** difficulty across rounds

### Key Concepts

#### 1. Multi-Round Structure

```
start_session():
│
├─ Get topic from user (e.g., "recursion")
├─ Get language preference (e.g., "Python")
│
└─ For each round (up to 5):
    │
    ├─ 1. Generate flawed code
    │   └─ API call with special prompt
    │
    ├─ 2. Display code + student question
    │   └─ Syntax highlighting with Rich
    │
    ├─ 3. Get user's teaching hints
    │   └─ Prompt for guidance
    │
    ├─ 4. Evaluate hints
    │   └─ AI roleplays as student responding to hints
    │
    ├─ 5. Display evaluation
    │   └─ Show student's response
    │
    └─ 6. Check understanding
        ├─ If YES: Offer new problem
        └─ If NO: Continue with related example
```

#### 2. Progressive Difficulty

```python
if self.round_number == 1:
    difficulty = "obvious but instructive"
elif self.round_number <= 3:
    difficulty = "subtle and thought-provoking"
else:
    difficulty = "nuanced and requiring deep understanding"
```

**🔍 Why**: Start easy, build confidence, then challenge.

#### 3. Code Generation Prompt Pattern

```
Generate code with:
1. Instructive mistake (teaches a concept)
2. Clever mistake (not immediately obvious)
3. Realistic mistake (programmers actually make)
4. Focused mistake (ONE specific misconception)

Format:
## Code
[flawed code]

## Student Question
[authentic question from student perspective]

## Hidden Issues
[what's actually wrong - internal notes]
```

**💡 Key insight**: The "Student Question" makes it feel like a real teaching scenario.

#### 4. Evaluation Pattern

The AI roleplays as a student:

```
You are a student. Teacher gave these hints: "{user_hints}"

Respond as student:
- If hints were good: Show you're getting closer
- If they gave answer directly: Note it would be better to discover yourself
- If too vague: Ask for clarification

Assessment: Were hints appropriately scaffolded?
Understanding Achieved: YES/NO
```

**🎯 This creates a realistic teaching simulation**.

#### 5. Conversation History Across Rounds

```python
self.conversation_history = []

# Round 1
self.conversation_history.append({"role": "user", "content": "Generate code about X"})
self.conversation_history.append({"role": "assistant", "content": "[Code 1]"})

# Round 2 - Claude remembers Round 1!
self.conversation_history.append({"role": "user", "content": "Generate another example"})
# Claude will generate related but different example
```

**💡 Why maintain history**: Each round builds on previous rounds.

---

## cli.py - Command-Line Interface

### Purpose
The entry point that routes commands to the right workflows.

### Key Concepts

#### 1. Click Framework Basics

**Command Group**:
```python
@click.group()
@click.version_option(version="0.1.0")
def main():
    """Code Tutor - Description"""
    pass
```

**Individual Commands**:
```python
@main.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--recursive/--no-recursive", default=True)
def review(path: str, recursive: bool):
    """Review a source code file or directory."""
    # Implementation
```

**🔍 Decorators**:
- `@click.group()` - Creates command group
- `@click.command()` - Adds command to group
- `@click.argument()` - Required positional argument
- `@click.option()` - Optional flag or value
- `@click.pass_context` - Passes Click context (for invoking other commands)

#### 2. Setup Wizard Pattern

The `setup` command is a multi-step wizard:

```
setup():
│
├─ Welcome message
│
├─ Step 1: API Key
│   ├─ Check if existing key
│   ├─ Prompt (with password hiding)
│   └─ Validate non-empty
│
├─ Step 2: Model Selection
│   ├─ Display options (Sonnet vs Haiku)
│   ├─ Prompt for choice (1 or 2)
│   └─ Map to model name
│
├─ Step 3: Experience Level
│   ├─ Display options (beginner/intermediate/advanced/expert)
│   └─ Prompt for choice
│
├─ Step 4: Question Style
│   ├─ Display styles (Socratic/Direct/Exploratory)
│   └─ Prompt for choice
│
├─ Step 5: Focus Areas
│   ├─ Display areas (design/readability/performance/etc.)
│   ├─ Accept comma-separated input (e.g., "1,2,4")
│   └─ Parse and validate
│
├─ Step 6: Logging
│   └─ Confirm yes/no
│
└─ Save Configuration
    ├─ Build config dict
    ├─ config_manager.save()
    └─ Display success message
```

**🎯 Pattern**: Progressive disclosure - one question at a time.

#### 3. Configuration Checking Pattern

```python
def review(path: str, ...):
    # Load config
    config_manager = ConfigManager()
    config_manager.load()

    # Check if configured
    if not config_manager.is_configured():
        console.print(
            "[red]Error:[/red] Not configured.\n"
            "Run 'code-tutor setup' first."
        )
        sys.exit(1)

    # Proceed with review...
```

**💡 Fail fast**: Check configuration before attempting work.

#### 4. Click Context for Command Invocation

```python
@main.command()
@click.pass_context
def config(ctx, config_dir: Optional[str]):
    """View or update configuration."""

    # Display current config...

    # Offer to reconfigure
    if Confirm.ask("Would you like to reconfigure?"):
        # Invoke setup command using context
        ctx.invoke(setup, config_dir=config_dir)
```

**🔍 Why**: Reuse setup logic instead of duplicating.

#### 5. Rich Formatting Throughout

**Info Panel**:
```python
console.print(Panel.fit(
    "[bold cyan]Code Tutor v0.1.0[/bold cyan]\n\n"
    "Features:\n"
    "• Personalized feedback\n"
    "• Interactive dialogue\n"
    "...",
    border_style="cyan",
))
```

**Progress Indicators**:
```python
console.print("[cyan]Analyzing code...[/cyan]")
# Do work
console.print("[green]✓ Complete![/green]")
```

**Color Coding**:
- `[cyan]` - Info/instructions
- `[green]` - Success
- `[yellow]` - Warnings
- `[red]` - Errors
- `[dim]` - Less important info

---

## Patterns Used Across All Three Files

### 1. Dependency Injection

```python
class Session:
    def __init__(self, config_manager, console):
        self.config = config_manager  # Inject, don't create
        self.console = console        # Inject, don't create
```

**Benefits**:
- Easy testing (can inject mocks)
- Flexible configuration
- Clear dependencies

### 2. Early Returns

```python
def do_something(self):
    if not self.enabled:
        return  # Exit early if disabled

    # Main logic here
```

**Benefits**:
- Reduces nesting
- Makes conditions clear
- Improves readability

### 3. Try-Except-Finally for Resources

```python
try:
    session = create_session()
    session.run()
except KeyboardInterrupt:
    console.print("Interrupted by user")
finally:
    if logger:
        logger.end_session()  # Always clean up
```

### 4. Rich Console Everywhere

Instead of `print()`, use `console.print()` with Rich markup:

```python
# Bad
print("Error: File not found")

# Good
console.print("[red]Error:[/red] File not found")
```

### 5. Configuration-Driven Behavior

```python
# Let config determine behavior
if self.config.is_logging_enabled():
    self.logger = SessionLogger(...)

if self.config.should_log_interactions():
    self.logger.log_user_input(...)
```

---

## How to Read the Source Files

Since these files are long (200-500 lines), here's how to approach them:

### session.py
1. Read `__init__` - see what components it uses
2. Read `start_review()` - understand the main flow
3. Read helper methods (`_display_observations`, `_ask_questions`)
4. Read `review_directory()` - see how it extends to multiple files

### teaching_session.py
1. Read `start_session()` - main flow
2. Read `_run_teaching_rounds()` - the round loop
3. Read `_generate_flawed_code()` - code generation
4. Read `_evaluate_explanation()` - evaluation logic
5. Read parsing methods

### cli.py
1. Read `main()` - the command group
2. Read `setup()` - configuration wizard
3. Read `review()` - how it creates ReviewSession
4. Read `teach_me()` - how it creates TeachingSession
5. Read `export_logs()` - utility command

---

## Questions to Think About

### Design Questions

1. **Why separate ReviewSession and TeachingSession classes?**
   - Could they share a base class? What would it contain?

2. **Why inject console into Session classes?**
   - What if we used `print()` directly?

3. **Why use Rich instead of plain text?**
   - What's the trade-off in dependencies vs. UX?

4. **Why Click instead of argparse?**
   - What makes Click better for this use case?

5. **Why is logging optional?**
   - What if it was always on? Always off?

### Implementation Questions

1. **What happens if API call fails mid-session?**
   - Where is error handling?
   - How is state maintained?

2. **How does conversation history grow?**
   - Could it exceed API limits?
   - Should there be truncation?

3. **What if user Ctrl+C during input?**
   - Where is KeyboardInterrupt handled?
   - Is cleanup guaranteed?

4. **How does follow-up dialogue work?**
   - Why is it a while loop?
   - How to exit gracefully?

5. **What makes code generation prompts effective?**
   - What if mistakes are too obvious/subtle?
   - How is difficulty calibrated?

---

## Next Steps

1. **Read the four annotated core files** (config, file_reader, analyzer, logger)

2. **Run the application**:
   ```bash
   code-tutor setup  # Configure
   code-tutor review examples/calculator.py  # Try review
   code-tutor teach-me  # Try teaching mode
   ```

3. **Read the source files**:
   - `src/code_tutor/session.py`
   - `src/code_tutor/teaching_session.py`
   - `src/code_tutor/cli.py`

4. **Experiment**:
   - Modify a prompt
   - Add a new command
   - Change the display format
   - Add a feature

5. **Build your own**:
   - Different domain (writing tutor, math tutor)
   - Different AI (different API)
   - Different interface (web, mobile)

---

## Summary

These three orchestration files show you how to:

✅ **Build complete workflows** from simple components
✅ **Create beautiful CLI experiences** with Rich
✅ **Handle user interaction** with prompts and confirmations
✅ **Manage complex state** across multi-step processes
✅ **Implement role-playing** with AI
✅ **Design progressive experiences** (wizards, rounds)

The patterns here apply far beyond this specific project!

Happy coding! 🚀
