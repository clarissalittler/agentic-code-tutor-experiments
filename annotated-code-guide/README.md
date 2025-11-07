# Code Tutor - Annotated Code Guide

Welcome! This directory contains heavily commented versions of all the main code files from the Code Tutor project, along with this guide to help you understand how to build a similar CLI tool yourself.

## 📚 What You'll Learn

By studying these annotated files, you'll learn how to:

1. **Build CLI applications** using Click framework
2. **Integrate AI APIs** (specifically Anthropic's Claude) into your applications
3. **Manage user configuration** with JSON-based config files
4. **Create interactive workflows** with conversation history and state management
5. **Format beautiful terminal output** using Rich library
6. **Implement logging systems** for debugging and analytics
7. **Handle file I/O** with proper encoding detection and error handling
8. **Parse and structure LLM responses** from conversational AI
9. **Design educational software** with adaptive, respectful feedback

## 🗺️ Reading Order

I recommend reading the files in this order to build your understanding progressively:

### **Level 1: Foundation** (Start Here!)

1. **`config.py`** - Configuration management
   - **Why first?** Understanding how configuration works is fundamental. This is the simplest file.
   - **Key concepts:** JSON file I/O, dot-notation access, validation patterns
   - **Time:** ~15-20 minutes

2. **`file_reader.py`** - File utilities
   - **Why second?** Learn file handling before processing content
   - **Key concepts:** File type detection, encoding handling, metadata extraction
   - **Time:** ~20 minutes

### **Level 2: Core Integration** (Building Up)

3. **`analyzer.py`** - Claude API integration
   - **Why third?** This is the "brain" of the application - understanding API calls is crucial
   - **Key concepts:** API client usage, prompt engineering, response parsing, conversation history
   - **Time:** ~30-40 minutes
   - **⚠️ Most complex concepts here!** Take your time

4. **`logger.py`** - Interaction logging
   - **Why fourth?** Supporting infrastructure that other components use
   - **Key concepts:** JSONL format, event logging, session tracking
   - **Time:** ~15 minutes

### **Level 3: User-Facing Workflows** (Putting It Together)

5. **`session.py`** - Code review workflow
   - **Why fifth?** See how everything comes together in an interactive session
   - **Key concepts:** Workflow orchestration, user interaction loops, Rich formatting
   - **Time:** ~30 minutes

6. **`teaching_session.py`** - Teaching mode workflow
   - **Why sixth?** Advanced workflow with role-playing and evaluation
   - **Key concepts:** Multi-round conversations, code generation, Socratic method implementation
   - **Time:** ~30 minutes

### **Level 4: Entry Point** (The Big Picture)

7. **`cli.py`** - Command-line interface
   - **Why last?** Once you understand all the components, see how they're orchestrated from the CLI
   - **Key concepts:** Click command groups, configuration wizards, command routing
   - **Time:** ~30-40 minutes

**Total learning time: ~3-4 hours** (take breaks!)

## 🎯 What This Project Does

**Code Tutor** is an AI-powered CLI tool with two modes:

### Code Review Mode
```bash
code-tutor review my_code.py
```
- Analyzes your code respectfully
- Asks clarifying questions before criticizing
- Adapts feedback to your experience level
- Supports follow-up dialogue

### Teaching Mode (Socratic Learning)
```bash
code-tutor teach-me
```
- You teach the AI by explaining code mistakes
- AI generates intentionally flawed code
- You provide hints and guidance (as a teacher would)
- AI evaluates your understanding
- Progresses through multiple rounds

## 🏗️ Architecture Overview

```
User Input (CLI)
      ↓
┌─────────────────────────────────────┐
│  cli.py - Command Router            │
│  (setup, review, teach-me, config)  │
└──────────────┬──────────────────────┘
               │
      ┌────────┴────────┐
      ↓                 ↓
┌──────────────┐  ┌──────────────────┐
│ session.py   │  │teaching_session.py│
│ Review Mode  │  │  Teaching Mode    │
└──────┬───────┘  └────────┬──────────┘
       │                   │
       └─────────┬─────────┘
                 ↓
         ┌──────────────┐
         │ analyzer.py  │
         │ Claude API   │
         └──────┬───────┘
                │
    ┌───────────┼───────────┐
    ↓           ↓           ↓
┌─────────┐ ┌────────┐ ┌─────────┐
│config.py│ │file_   │ │logger.py│
│         │ │reader  │ │         │
└─────────┘ └────────┘ └─────────┘
```

## 🧩 Component Responsibilities

| File | Purpose | Main Concepts |
|------|---------|---------------|
| **cli.py** | Entry point, command routing | Click framework, user prompts, command groups |
| **config.py** | Configuration management | JSON I/O, validation, default values |
| **file_reader.py** | File I/O and metadata | File type detection, encoding, language identification |
| **analyzer.py** | Claude API integration | HTTP API calls, prompt engineering, parsing responses |
| **session.py** | Code review orchestration | Workflow state, conversation loops, Rich formatting |
| **teaching_session.py** | Teaching mode orchestration | Multi-round dialogue, role-playing, evaluation logic |
| **logger.py** | Event logging | JSONL format, session tracking, event types |

## 🔑 Key Technologies & Why They Were Chosen

### **Click** (CLI Framework)
- **What:** Creates command-line interfaces with minimal boilerplate
- **Why:** Automatic help generation, type validation, nested commands, interactive prompts
- **Alternatives:** argparse (more verbose), typer (similar but newer)

### **Anthropic SDK** (AI Integration)
- **What:** Official Python client for Claude API
- **Why:** Reliable, well-documented, handles authentication and retries
- **Key feature:** Message-based conversation API with system prompts

### **Rich** (Terminal Formatting)
- **What:** Library for beautiful terminal output
- **Why:** Panels, tables, markdown rendering, syntax highlighting out-of-the-box
- **Alternatives:** colorama (simpler), termcolor (basic), blessed (complex)

### **pathlib** (File Paths)
- **What:** Object-oriented filesystem paths
- **Why:** Cross-platform compatibility, cleaner than os.path
- **Modern Python:** Preferred over os.path in Python 3.4+

### **JSON** (Configuration Storage)
- **What:** Human-readable structured data format
- **Why:** Easy to edit manually, widely supported, nested structures
- **Alternatives:** YAML (more features), TOML (simpler), INI (flat)

## 💡 Design Patterns Used

### 1. **Configuration Manager Pattern**
- **Where:** `config.py`
- **What:** Centralized configuration with validation
- **Why:** Single source of truth, consistent access, easy testing

### 2. **Session Pattern**
- **Where:** `session.py`, `teaching_session.py`
- **What:** Encapsulate workflow state and conversation history
- **Why:** Isolates state, enables multi-turn conversations, easier debugging

### 3. **Facade Pattern**
- **Where:** `analyzer.py` wraps Anthropic API
- **What:** Simplified interface to complex subsystem
- **Why:** Hides API complexity, makes code more testable, easier to swap APIs

### 4. **Strategy Pattern** (implicit)
- **Where:** Different question styles, experience levels
- **What:** Encapsulates algorithms (feedback strategies)
- **Why:** Flexible behavior changes without code modification

### 5. **Event Logging Pattern**
- **Where:** `logger.py`
- **What:** Structured event recording with timestamps
- **Why:** Debugging, analytics, user behavior understanding

## 🛠️ How to Build Something Similar

### Step 1: Set Up Your Project Structure
```bash
mkdir my-cli-tool
cd my-cli-tool
python -m venv venv
source venv/bin/activate
pip install click anthropic rich
```

### Step 2: Start with Configuration
- Read `config.py` first
- Create a simple config manager that loads/saves JSON
- Add validation for your specific config needs

### Step 3: Create Your CLI Entry Point
- Read `cli.py` sections on Click usage
- Start with a single command
- Add more commands as you build features

### Step 4: Integrate Claude API
- Read `analyzer.py` carefully
- Study the prompt engineering techniques
- Start with simple prompts, iterate to improve
- Pay attention to response parsing

### Step 5: Build Your Workflow
- Read `session.py` or `teaching_session.py` based on your needs
- Design your conversation flow
- Implement state management
- Add Rich formatting for better UX

### Step 6: Add Logging (Optional but Recommended)
- Read `logger.py`
- Implement event logging from day 1
- Makes debugging much easier later

## 📖 Code Reading Tips

### Understanding Annotations

Each annotated file contains:

1. **File-level overview** - What the file does and why it exists
2. **Import explanations** - Why each library is used
3. **Class/function docstrings** - Purpose and high-level approach
4. **Inline comments** - Line-by-line explanations of complex logic
5. **Design notes** - Why certain decisions were made
6. **Learning callouts** - Key concepts highlighted with 🔍, 💡, ⚠️

### Symbols Used in Annotations

- 🔍 **Key Concept** - Important pattern or technique to understand
- 💡 **Design Decision** - Why something was done this way
- ⚠️ **Common Pitfall** - Easy mistake to avoid
- 🎯 **Best Practice** - Recommended approach
- 🔗 **Connection** - How this relates to other parts of the codebase
- 📚 **Further Learning** - Topics to explore more deeply

### Active Reading Strategy

1. **First Pass:** Read the file-level overview and skim the structure
2. **Second Pass:** Read function signatures and docstrings
3. **Third Pass:** Dive into implementation details with inline comments
4. **Fourth Pass:** Try to explain the code to yourself in your own words

## 🎓 Learning Exercises

After reading each file, try these exercises:

### After `config.py`:
- [ ] Create your own config manager with different fields
- [ ] Add a new validation rule
- [ ] Implement a "reset to defaults" feature

### After `file_reader.py`:
- [ ] Add support for a new file type
- [ ] Write a function to count total files in a directory
- [ ] Handle binary files gracefully

### After `analyzer.py`:
- [ ] Write a different prompt for a different use case
- [ ] Parse a more complex structured response
- [ ] Add retry logic for API failures

### After `session.py`:
- [ ] Design a workflow for a different domain (e.g., writing tutor)
- [ ] Add a "save session transcript" feature
- [ ] Implement session resumption

### After `teaching_session.py`:
- [ ] Create a different teaching scenario (e.g., debugging practice)
- [ ] Add difficulty progression
- [ ] Implement hints system

### After `cli.py`:
- [ ] Add a new command to the CLI
- [ ] Create a configuration wizard for your own app
- [ ] Add command-line flags for common options

## 🔧 Common Patterns You'll See

### Pattern: Click Command with Confirmation
```python
@click.command()
@click.option('--yes', '-y', is_flag=True)
def dangerous_operation(yes):
    if not yes:
        if not click.confirm("Are you sure?"):
            return
    # do operation
```

### Pattern: Rich Panel Output
```python
from rich.console import Console
from rich.panel import Panel

console = Console()
console.print(Panel("Content here", title="Title"))
```

### Pattern: Config Dot Notation Access
```python
# Instead of: config["preferences"]["verbosity"]
# Use: config.get("preferences.verbosity")
```

### Pattern: JSONL Event Logging
```python
event = {"timestamp": ..., "type": "event_type", "data": {...}}
with open(log_file, 'a') as f:
    f.write(json.dumps(event) + '\n')
```

### Pattern: API Conversation History
```python
messages = []
messages.append({"role": "user", "content": "question"})
response = client.messages.create(model="...", messages=messages)
messages.append({"role": "assistant", "content": response.content[0].text})
```

## 🚀 Next Steps After Learning

Once you've gone through all the annotated files:

1. **Try modifying the code**
   - Add a new command
   - Change the prompts
   - Add a new configuration option

2. **Build your own variation**
   - Writing tutor instead of code tutor
   - Math problem explainer
   - Language learning assistant

3. **Extend the project**
   - Add support for comparing multiple files
   - Create a web interface
   - Add team/shared configurations

4. **Explore related topics**
   - Advanced prompt engineering
   - LLM fine-tuning
   - Building AI agents
   - Testing AI-powered applications

## 📚 Additional Resources

### Click (CLI Framework)
- Official docs: https://click.palletsprojects.com/
- Tutorial: https://click.palletsprojects.com/en/8.1.x/quickstart/

### Anthropic Claude API
- Official docs: https://docs.anthropic.com/
- Prompt engineering guide: https://docs.anthropic.com/claude/docs/prompt-engineering

### Rich (Terminal Formatting)
- Official docs: https://rich.readthedocs.io/
- Examples gallery: https://github.com/Textualize/rich#rich-library

### Python Best Practices
- "Effective Python" by Brett Slatkin
- "Fluent Python" by Luciano Ramalho
- "Python Cookbook" by David Beazley

## ❓ FAQ

**Q: Do I need to understand everything in one reading?**
A: No! This is meant to be a reference. Read at your own pace, come back to sections as needed.

**Q: What if I don't understand a specific concept?**
A: Look for the 📚 Further Learning callouts. Also feel free to ask questions or research the specific topic.

**Q: Can I modify the annotated code?**
A: Yes! Try things out, break things, fix them. That's how you learn.

**Q: Should I memorize the code?**
A: No. Focus on understanding the patterns and principles. The specific syntax will come with practice.

**Q: What if I want to build something completely different?**
A: Great! The patterns here (CLI, API integration, config management, etc.) apply to many different projects.

## 🙏 Final Notes

This codebase was written with educational principles in mind:
- **Respectful feedback** over criticism
- **Understanding context** before judging
- **Adaptive learning** based on skill level
- **Socratic method** for deeper learning

These same principles apply to learning this code:
- Take your time
- Don't judge yourself for not understanding immediately
- Context matters - some concepts build on others
- Ask questions and experiment

Happy learning! 🎉

---

*Remember: Every expert was once a beginner. The goal isn't to understand everything perfectly on the first pass, but to build understanding progressively through reading, experimentation, and practice.*
