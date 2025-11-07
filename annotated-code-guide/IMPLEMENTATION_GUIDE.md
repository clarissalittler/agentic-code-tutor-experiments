# Implementation Guide - How the Pieces Fit Together

This guide explains how all the components work together to create the Code Tutor application.

## The Four Fully Annotated Core Files

We've created **heavily annotated** versions of the four core foundation files:

### 1. **config.py** - Configuration Management
- **Read this first!** (15-20 minutes)
- Learn: JSON I/O, dot-notation access, validation
- Pattern: Configuration Manager
- Creates: `~/.config/code-tutor/config.json`

### 2. **file_reader.py** - File I/O Utilities
- **Read second** (20 minutes)
- Learn: File type detection, encoding handling, directory traversal
- Supports: 25+ programming languages
- Key method: `read_file()` returns code + metadata

### 3. **analyzer.py** - Claude API Integration
- **Read third** (30-40 minutes) - **Most complex!**
- Learn: Prompt engineering, API integration, conversation history
- Pattern: Facade Pattern
- Core workflow: `analyze_code()` → `process_answers()` → `continue_conversation()`

### 4. **logger.py** - Event Logging
- **Read fourth** (15 minutes)
- Learn: JSONL format, event logging, session tracking
- Format: One JSON object per line
- Exports: All sessions to single JSON file

## How They Work Together

### Review Mode Workflow

```
User runs: code-tutor review example.py

┌─────────────────────────────────────────────────────────────────┐
│ 1. CLI (cli.py)                                                  │
│    - Parses command-line arguments                              │
│    - Creates ReviewSession                                       │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│ 2. ConfigManager (config.py)                                     │
│    - Loads ~/.config/code-tutor/config.json                     │
│    - Gets API key, experience level, preferences                │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│ 3. SessionLogger (logger.py)                                     │
│    - Starts session logging                                     │
│    - Records session_start event                                │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│ 4. FileReader (file_reader.py)                                   │
│    - Reads example.py                                           │
│    - Detects language (Python)                                  │
│    - Extracts metadata (lines: 50, size: 1234 bytes)           │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│ 5. CodeAnalyzer (analyzer.py)                                    │
│    - Builds prompt with code + context                          │
│    - Calls Claude API                                           │
│    - Parses response into questions + observations             │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│ 6. ReviewSession (session.py)                                    │
│    - Displays observations in Rich panel                        │
│    - Asks user each question                                    │
│    - Collects answers                                           │
│    - Logs each Q&A pair                                         │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│ 7. CodeAnalyzer (analyzer.py) - SECOND CALL                     │
│    - process_answers() with full conversation history          │
│    - Claude generates personalized feedback                     │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│ 8. ReviewSession (session.py)                                    │
│    - Displays feedback as markdown                              │
│    - Offers follow-up Q&A loop                                  │
│    - Each follow-up uses continue_conversation()               │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│ 9. SessionLogger (logger.py)                                     │
│    - Logs session_end event                                     │
│    - Saves all events to JSONL file                            │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow Example

Let's trace a real example through the system:

### Input
```bash
code-tutor review calculator.py
```

### Step-by-Step

**1. Config Load** (`config.py`)
```python
{
  "api_key": "sk-ant-...",
  "model": "claude-sonnet-4-5",
  "experience_level": "intermediate",
  "preferences": {
    "question_style": "socratic",
    "focus_areas": ["design", "readability"]
  }
}
```

**2. File Read** (`file_reader.py`)
```python
{
  "path": "/home/user/calculator.py",
  "name": "calculator.py",
  "content": "def add(a, b):\n    return a + b\n...",
  "metadata": {
    "language": "Python",
    "line_count": 42,
    "size_bytes": 856
  }
}
```

**3. Initial Analysis** (`analyzer.py`)
```python
# Prompt built:
"""
You are a respectful, thoughtful code tutor...
Programmer Profile:
- Experience Level: intermediate
- Focus Areas: design, readability
File: calculator.py (Python, 42 lines)
Code: [code here]
...
"""

# Response parsed:
{
  "questions": [
    "What led you to structure the calculator functions separately?",
    "How do you plan to handle invalid inputs?"
  ],
  "observations": [
    "Functions follow single-responsibility principle",
    "Clear naming conventions used throughout"
  ]
}
```

**4. User Interaction** (`session.py`)
```
Displays observations, asks questions, collects answers
```

**5. Feedback Generation** (`analyzer.py`)
```python
# Second API call with full conversation history:
messages = [
  {"role": "user", "content": "... [initial prompt]"},
  {"role": "assistant", "content": "... [questions + observations]"},
  {"role": "user", "content": "... [answers]"}
]

# Returns personalized feedback based on user's explanations
```

**6. Logging** (`logger.py`)
```jsonl
{"event_type":"session_start","timestamp":"2025-01-15T10:00:00","session_id":"abc123",...}
{"event_type":"code_analysis","timestamp":"2025-01-15T10:00:05","file_path":"calculator.py",...}
{"event_type":"ai_response","response_type":"question","content":"What led you...",...}
{"event_type":"user_input","input_type":"answer","content":"I chose this because...",...}
{"event_type":"ai_response","response_type":"feedback","content":"**Positive Feedback**...",...}
{"event_type":"session_end","timestamp":"2025-01-15T10:05:30","duration_seconds":330}
```

## The Three Other Important Files

While we've focused on the four core files, the complete application has three more files that orchestrate everything:

### session.py - Code Review Orchestration
**Purpose**: Manages the interactive code review workflow

**Key Responsibilities**:
- Initialize all components (config, file reader, analyzer, logger)
- Orchestrate the review flow:
  1. Read file
  2. Display observations
  3. Ask questions and collect answers
  4. Generate and display feedback
  5. Handle follow-up dialogue
- Format output with Rich library (panels, markdown)

**Main Method**: `start_review(file_path)`

### teaching_session.py - Teaching Mode Orchestration
**Purpose**: Implements the "Teach Me!" Socratic learning mode

**Key Responsibilities**:
- Generate intentionally flawed code
- Present as "student question"
- Collect user's teaching hints
- Evaluate hints (AI roleplays as student)
- Run multiple teaching rounds

**Unique Feature**: Role reversal - user teaches AI

**Main Method**: `start_session()`

### cli.py - Command-Line Interface
**Purpose**: Entry point for the application

**Commands**:
- `setup` - Initial configuration wizard
- `review` - Review code files
- `teach-me` - Teaching mode
- `config` - View/update configuration
- `export-logs` - Export session logs
- `info` - Show information

**Framework**: Click (command-line framework)

**Output**: Rich formatting (panels, colors, markdown)

## How to Build Something Similar

### Starting Point: The Essential Three

If you want to build a similar AI-powered CLI tool, start with these three patterns:

1. **Configuration Manager** (config.py)
   ```python
   class ConfigManager:
       def load() -> dict
       def save(config: dict) -> None
       def get(key: str) -> any
   ```

2. **API Integration** (analyzer.py)
   ```python
   class APIClient:
       def __init__(api_key: str)
       def call_api(prompt: str) -> dict
       def maintain_conversation_history()
   ```

3. **CLI Entry Point** (cli.py)
   ```python
   import click

   @click.group()
   def main():
       pass

   @main.command()
   def your_command():
       # Load config
       # Call API
       # Display results
   ```

### Then Add

4. **Logging** (if you need debugging)
5. **File handling** (if working with files)
6. **Session management** (if multi-step workflows)

## Quick Reference: Method Calls

### Typical Review Session

```python
# 1. Load configuration
config = ConfigManager()
config.load()

# 2. Read file
reader = FileReader()
file_data = reader.read_file("example.py")

# 3. Initialize analyzer
analyzer = CodeAnalyzer(
    api_key=config.get_api_key(),
    model=config.get_model()
)

# 4. Analyze code
result = analyzer.analyze_code(
    code=file_data["content"],
    file_metadata=file_data["metadata"],
    experience_level=config.get("experience_level"),
    preferences=config.get("preferences")
)

# 5. Display questions, collect answers
questions = result["questions"]
answers = collect_answers_from_user(questions)

# 6. Generate feedback
feedback = analyzer.process_answers(
    answers=answers,
    experience_level=config.get("experience_level"),
    preferences=config.get("preferences")
)

# 7. Display feedback
display_feedback(feedback["feedback"])

# 8. Optional: Follow-up
while user_has_question:
    response = analyzer.continue_conversation(user_question)
    display_response(response)
```

## Common Patterns Used

### 1. Builder Pattern (Prompts)
```python
def _build_prompt(context):
    return f"""
    Role: {context.role}
    Context: {context.background}
    Task: {context.task}
    Format: {context.format}
    """
```

### 2. State Machine (Parsing)
```python
current_section = None
for line in lines:
    if line.startswith("##"):
        current_section = extract_section(line)
    elif current_section == "questions":
        questions.append(line)
    elif current_section == "observations":
        observations.append(line)
```

### 3. Conversation History
```python
messages = []
messages.append({"role": "user", "content": prompt})
response = api_call(messages)
messages.append({"role": "assistant", "content": response})
# Repeat for multi-turn dialogue
```

### 4. Event Logging
```python
def log_event(event_type, data):
    event = {
        "timestamp": datetime.now().isoformat(),
        "type": event_type,
        "data": data
    }
    log_file.write(json.dumps(event) + "\n")
```

## Next Steps

1. **Read the four annotated core files** in order
2. **Run the actual application** to see it in action
3. **Experiment** - modify prompts, add features
4. **Build your own** - adapt patterns to your use case

## Questions to Explore

As you read the code, think about:

1. **Why dot-notation access?** (config.py)
   - What are the trade-offs vs. nested dict access?

2. **Why JSONL vs. JSON?** (logger.py)
   - When would you choose each format?

3. **Why conversation history?** (analyzer.py)
   - Could you build this without it? What would change?

4. **Why ask questions before feedback?** (design principle)
   - How does this improve the interaction?

5. **Why separate session classes?** (session.py vs teaching_session.py)
   - Could they be combined? Why or why not?

---

**Remember**: The best way to learn is to:
1. Read the annotated code
2. Run the application
3. Modify something small
4. Observe what changes
5. Repeat!

Happy learning! 🎉
