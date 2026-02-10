# Code Tutor - Agentic Code Tutor Experiments

An intelligent, respectful code review and tutoring CLI tool powered by pluggable LLM providers.

This repository is a place to experiment with building command-line and local web interfaces for code tutoring, leveraging LLM-assisted development.

## Overview

Code Tutor provides three primary learning modes:

### 1. Code Review Mode
Personalized, educational code reviews that respect your programming style and experience level. Unlike traditional linters or code reviewers that simply point out issues, Code Tutor:

- **Asks questions** to understand your design decisions before providing feedback
- **Respects your style** and intentions while offering helpful suggestions
- **Adapts to your level** - whether you're a beginner or an expert
- **Encourages learning** through interactive dialogue

### 2. Teaching Mode (Teach Me!)
Learn by correcting mistakes through the Socratic method:

- **Presents flawed code** with intentional, clever mistakes
- **You explain** what's wrong and why it's a problem
- **AI evaluates** your understanding and provides feedback
- **Iterative learning** - dig deeper if your explanation needs refinement
- **Topic-focused** - Choose what you want to learn about

### 3. Roguelike Mode
Generate persistent homework-style challenge runs and grade them later:

- **Generate runs by topic** with language/type/difficulty controls
- **Persist to disk** so you can pause and resume across sessions
- **Reveal hints progressively** when you get stuck
- **Grade your solution later** with AI review once you're ready
- **Archive completed runs** to keep your workspace clean

## Features

- 🤔 **Interactive questioning** - Understands your code before critiquing
- 🎓 **Experience-aware** - Tailors feedback to your skill level
- 🎨 **Style-respecting** - Works with your coding style, not against it
- 💬 **Conversational** - Ask follow-up questions and dive deeper
- 🔧 **Configurable** - Set your preferences for question style and focus areas
- 🔌 **Provider-agnostic** - Works with Anthropic and OpenAI-compatible endpoints
- ♻️ **Resilient calls** - Retries transient provider/network failures automatically
- 📐 **Contract-driven parsing** - Shared JSON prompt contracts with resilient fallback parsing
- 🧱 **Service-layer orchestration** - Mode orchestration is decoupled from CLI handlers
- 📁 **Multi-file support** - Review individual files or entire directories
- 🧑‍🏫 **Teach Me Mode** - Learn by teaching and correcting flawed code
- 🕹️ **Roguelike Mode** - Persistent challenge runs with delayed grading

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/yourusername/agentic-code-tutor-experiments.git
cd agentic-code-tutor-experiments

# Install in development mode
pip install -e .
```

### Requirements

- Python 3.9 or higher
- An API key for your selected provider (Anthropic, OpenAI-compatible, etc.)

## Quick Start

### 1. Initial Setup

Configure Code Tutor with your API key and preferences:

```bash
code-tutor setup
```

You'll be prompted to provide:
- Your LLM provider (Anthropic or OpenAI-compatible)
- Your provider API key
- Your preferred model
- Optional custom base URL (for OpenAI-compatible endpoints)
- Your programming experience level (beginner/intermediate/advanced/expert)
- Your preferred question style (socratic/direct/exploratory)
- Focus areas for feedback (design, readability, performance, etc.)
- Logging preferences (unredacted logging requires explicit confirmation)

### 2. Review Your Code

Review a single file:

```bash
code-tutor review path/to/your/file.py
```

Review all files in a directory:

```bash
code-tutor review path/to/directory/
```

Review without recursing into subdirectories:

```bash
code-tutor review --no-recursive path/to/directory/
```

### 3. Learn with Teach Me Mode

Start an interactive teaching session:

```bash
code-tutor teach-me
```

In this mode:

1. Choose a topic you want to learn (e.g., "recursion", "async/await", "design patterns")
2. Select your preferred programming language
3. The AI presents intentionally flawed code
4. You explain what's wrong and why
5. The AI evaluates your understanding and provides feedback
6. If needed, it presents a refined example to deepen your learning

This Socratic method helps you learn by teaching - one of the most effective ways to master concepts!

### 4. Start a Roguelike Run

Generate a challenge run:

```bash
code-tutor roguelike generate "recursion" --language Python --type implementation
```

Check your saved runs:

```bash
code-tutor roguelike list
```

Read or resume a specific run:

```bash
code-tutor roguelike show <run-id>
```

Get graded when ready:

```bash
code-tutor roguelike grade <run-id>
```

Legacy alias: `code-tutor exercise ...` maps to the same roguelike commands.

### 5. Interactive Review Session

When you review code, Code Tutor will:

1. Read and analyze your code
2. Show initial observations
3. Ask clarifying questions about your design decisions
4. Generate personalized feedback based on your answers
5. Allow you to ask follow-up questions

## Configuration

### View Current Configuration

```bash
code-tutor config
```

### Configuration File

Configuration is stored in `~/.config/code-tutor/config.json`:

```json
{
  "provider": "anthropic",
  "api_key": "your-api-key",
  "api_key_locked": false,
  "model": "claude-sonnet-4-5",
  "base_url": "",
  "experience_level": "intermediate",
  "preferences": {
    "question_style": "socratic",
    "verbosity": "medium",
    "focus_areas": ["design", "readability"]
  },
  "logging": {
    "enabled": false,
    "log_interactions": true,
    "log_api_calls": false
  }
}
```

### Multi-Student Deployment (Locked API Key)

For classroom or multi-student environments where you want to provide a shared API key that students cannot modify, you can lock the API key in the configuration. This is useful when:

- Setting up Code Tutor on shared lab computers
- Providing a managed installation for students
- Controlling API usage through a single key

**Setup Instructions:**

1. **Create the configuration directory:**
   ```bash
   mkdir -p ~/.config/code-tutor
   ```

2. **Create a configuration file with locked API key:**
   ```bash
   cat > ~/.config/code-tutor/config.json <<'EOF'
   {
     "api_key": "your-shared-api-key",
     "api_key_locked": true,
     "model": "claude-sonnet-4-5",
     "experience_level": "intermediate",
     "preferences": {
       "question_style": "socratic",
       "verbosity": "medium",
       "focus_areas": ["design", "readability"]
     },
     "logging": {
       "enabled": false,
       "log_interactions": true,
       "log_api_calls": false
     }
   }
   EOF
   ```

3. **Set appropriate permissions** (optional but recommended):
   ```bash
   chmod 644 ~/.config/code-tutor/config.json
   ```

**Behavior with Locked API Key:**

- ✅ Students can still modify their experience level, question style, and other preferences
- ✅ Students can view the configuration with `code-tutor config`
- ✅ Students can use all features of Code Tutor normally
- ❌ Students cannot change the API key through `code-tutor setup`
- ℹ️  The configuration will clearly indicate that the API key is locked

When students run `code-tutor config`, they will see:

```
API key: ******* (locked)
Note: API key is locked for multi-student deployment.
```

**Note:** The API key is completely hidden (no characters are revealed) when locked to prevent students from seeing any part of the key.

When students try to reconfigure, they will be prompted:

```
Configuration is locked for multi-student deployment.
The API key cannot be changed. Other settings can be modified.

Do you want to modify non-API settings? [y/n]
```

**Alternative Deployment Using Custom Config Directory:**

You can also use a custom configuration directory for system-wide deployments:

```bash
# System-wide config location
sudo mkdir -p /etc/code-tutor
sudo nano /etc/code-tutor/config.json
# ... add configuration with api_key_locked: true

# Students then use:
code-tutor review --config-dir /etc/code-tutor myfile.py
```

### Experience Levels

- **Beginner** (0-1 years): Clear explanations, focus on fundamentals, avoid jargon
- **Intermediate** (1-3 years): Discuss trade-offs, introduce advanced concepts
- **Advanced** (3-5 years): Focus on architecture, design patterns, performance
- **Expert** (5+ years): Nuanced discussions about design philosophy and best practices

### Question Styles

- **Socratic**: Guides you to discover insights through leading questions
- **Direct**: Straightforward, specific questions about the code
- **Exploratory**: Open-ended questions about alternatives and trade-offs

### Available Models

Choose a provider and model:
- **anthropic**: Uses Claude models (e.g., `claude-sonnet-4-5`)
- **openai_compatible**: Uses OpenAI-style chat endpoints (e.g., `gpt-4o-mini`)

### Focus Areas

Choose what matters most to you:
- **Design**: Architecture and design patterns
- **Readability**: Code clarity and maintainability
- **Performance**: Efficiency and optimization
- **Security**: Security vulnerabilities and best practices
- **Testing**: Test coverage and quality
- **Documentation**: Comments and documentation

## Example Sessions

### Code Review Session

```bash
$ code-tutor review calculator.py

Reading file: calculator.py
Language: Python | Lines: 45 | Size: 1234 bytes

Analyzing code...

╭─ Initial Observations ─────────────────────────╮
│ • Clean class structure with clear method      │
│   separation                                    │
│ • Uses type hints for better code clarity      │
│ • Missing input validation in some methods     │
╰─────────────────────────────────────────────────╯

╭─ I have some questions about your code ────────╮
│ Please help me understand your design          │
│ decisions:                                      │
╰─────────────────────────────────────────────────╯

Question 1: I notice you're not validating inputs in the divide method. Was
this intentional, or would you like to handle division by zero?

Your answer: I was planning to add that but haven't gotten to it yet.

Question 2: You're using a class here - what led you to choose an
object-oriented approach rather than simple functions?

Your answer: I thought it would be more organized and easier to extend later
with more operations.

Generating personalized feedback...

╭─ Feedback & Suggestions ────────────────────────╮
│                                                  │
│ ## Positive Feedback                             │
│                                                  │
│ • Great use of type hints! This makes your code  │
│   much more maintainable...                      │
│                                                  │
│ ## Suggestions for Improvement                   │
│                                                  │
│ 1. **Input Validation**: Since you mentioned...  │
│                                                  │
╰──────────────────────────────────────────────────╯

Do you have any follow-up questions? (y/N): y

Your question: What's the best way to handle the division by zero error?

...
```

### Teaching Session (Teach Me!)

```bash
$ code-tutor teach-me

╭─────────────────────── 🎓 Teaching Mode ───────────────────────╮
│ Welcome to Teach Me!                                            │
│                                                                 │
│ In this mode, I'll show you code with intentional mistakes.    │
│ Your job is to identify and explain what's wrong.              │
│                                                                 │
│ The better your explanation, the more we'll learn together!    │
│ If your explanation needs refinement, I'll adjust the code     │
│ and we'll dig deeper into the concept.                         │
╰─────────────────────────────────────────────────────────────────╯

What would you like to learn about?
Examples: recursion, async/await, design patterns, memory management

Topic: recursion

Great! Let's explore recursion together.

Which programming language would you like to use?
Examples: Python, JavaScript, Java, C++, Go, Rust

Language [Python]:

════════════════════════════════════════════════════════════════
Round 1
════════════════════════════════════════════════════════════════

Here's some code for you to review:

╭────────────────────── Code ──────────────────────╮
│  1 def factorial(n):                              │
│  2     if n == 0:                                 │
│  3         return 1                               │
│  4     return n * factorial(n)                    │
╰───────────────────────────────────────────────────╯

What's wrong with this code? Please explain:
(Be specific about what the issue is and why it's a problem)

Your explanation: The base case checks if n equals 0, but the recursive
call doesn't decrement n, so it will call factorial(n) infinitely and
cause a stack overflow.

Teacher's Feedback:

╭─────────────────────────────────────────────────╮
│ ## Evaluation                                    │
│                                                  │
│ Excellent! You've correctly identified the      │
│ critical issue.                                  │
│                                                  │
│ ## Feedback                                      │
│                                                  │
│ ✓ You identified that n doesn't change          │
│ ✓ You recognized this causes infinite recursion │
│ ✓ You understood the consequence (stack         │
│   overflow)                                      │
│                                                  │
│ Your explanation demonstrates solid             │
│ understanding of how recursion works and what   │
│ happens when the recursive call doesn't         │
│ progress toward the base case.                  │
│                                                  │
│ ## Understanding Achieved                        │
│ YES                                              │
╰─────────────────────────────────────────────────╯

Excellent! You've demonstrated solid understanding of this aspect.

Continue with another example? [y/N]: y

════════════════════════════════════════════════════════════════
Round 2
════════════════════════════════════════════════════════════════

[...continues with more examples...]
```

## Supported Languages

Code Tutor supports reviewing code in:

Python, JavaScript, TypeScript, Java, C, C++, C#, Go, Rust, Ruby, PHP, Swift, Kotlin, Scala, Shell scripts, SQL, HTML, CSS, SCSS, Sass, JSON, YAML, XML, Markdown, R

## Development

### Project Structure

```
agentic-code-tutor-experiments/
├── src/
│   └── code_tutor/
│       ├── __init__.py
│       ├── cli.py              # Command-line interface and mode commands
│       ├── cli_support.py      # Shared CLI setup helpers
│       ├── modes.py            # Central mode metadata/aliases
│       ├── contracts.py        # Shared LLM prompt contracts + validators
│       ├── services.py         # Mode service orchestration layer
│       ├── config.py           # Configuration management
│       ├── analyzer.py         # Code analysis via provider abstraction
│       ├── response_parsing.py # Shared resilient response parsing helpers
│       ├── exercise_generator.py
│       ├── exercise_manager.py
│       ├── session.py          # Code review session management
│       ├── teaching_session.py # Teach Me mode
│       └── proof_session.py    # Proof review/teaching mode
├── tests/                      # Test files
├── DESIGN.md                  # Detailed design documentation
├── plan.org                   # Project planning and ideas
├── pyproject.toml             # Project configuration
└── README.md                  # This file
```

### Running in Development Mode

```bash
# Install with development dependencies
pip install -e ".[dev]"

# Run from source
python -m code_tutor.cli review your_file.py
```

### Testing

```bash
# Run tests
pytest

# Format code
black src/

# Lint code
ruff check src/
```

The test suite includes deterministic fake-LLM integration tests covering all primary modes.

## How It Works

1. **File Reading**: Code Tutor reads your source files and extracts metadata (language, size, structure)

2. **Initial Analysis**: Using your configured LLM provider, it performs an initial analysis to understand:
   - Overall code structure
   - Potential areas of interest
   - Design patterns used

3. **Interactive Questioning**: Instead of immediately critiquing, it asks clarifying questions:
   - What were you trying to achieve?
   - Why did you choose this approach?
   - Are there constraints or requirements I should know about?

4. **Personalized Feedback**: Based on your answers and experience level, it provides:
   - Positive reinforcement for good decisions
   - Actionable suggestions with explanations
   - Learning opportunities
   - Discussion of trade-offs

5. **Follow-up Dialogue**: You can ask questions and explore topics in more depth

## Philosophy

Code Tutor is built on these principles:

- **Respect First**: Assume the programmer has good reasons for their decisions
- **Question Before Judging**: Understand before critiquing
- **Teach, Don't Preach**: Focus on learning and growth
- **Adapt to the Learner**: Match feedback to experience level
- **Encourage Dialogue**: Learning is a conversation, not a lecture

## Roadmap

Future enhancements planned:

- [ ] Project-wide analysis across multiple files
- [ ] Git integration for reviewing changes
- [ ] Save and replay review sessions
- [ ] Support for multiple LLM backends
- [ ] Team configuration sharing
- [ ] Custom rule sets and style guides
- [ ] Integration with code editors
- [ ] Web interface option

## Contributing

Contributions are welcome! This is an experimental project exploring how AI can provide better, more educational code reviews.

## License

MIT License - see LICENSE file for details

## Acknowledgments

- Powered by [Anthropic's Claude](https://www.anthropic.com/claude)
- Built with [Click](https://click.palletsprojects.com/) and [Rich](https://rich.readthedocs.io/)

## Support

For issues, questions, or suggestions, please open an issue on GitHub.

---

**Note**: This is an experimental project exploring LLM-assisted development and agentic code tutoring interfaces.
