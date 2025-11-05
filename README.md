# Code Tutor - Agentic Code Tutor Experiments

An intelligent, respectful code review and tutoring CLI tool powered by Claude AI.

This repository is a place to experiment with building command-line and local web interfaces for code tutoring, leveraging LLM-assisted development.

## Overview

Code Tutor is designed to provide personalized, educational code reviews that respect your programming style and experience level. Unlike traditional linters or code reviewers that simply point out issues, Code Tutor:

- **Asks questions** to understand your design decisions before providing feedback
- **Respects your style** and intentions while offering helpful suggestions
- **Adapts to your level** - whether you're a beginner or an expert
- **Encourages learning** through interactive dialogue

## Features

- 🤔 **Interactive questioning** - Understands your code before critiquing
- 🎓 **Experience-aware** - Tailors feedback to your skill level
- 🎨 **Style-respecting** - Works with your coding style, not against it
- 💬 **Conversational** - Ask follow-up questions and dive deeper
- 🔧 **Configurable** - Set your preferences for question style and focus areas
- 📁 **Multi-file support** - Review individual files or entire directories

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
- An Anthropic API key ([get one here](https://console.anthropic.com/settings/keys))

## Quick Start

### 1. Initial Setup

Configure Code Tutor with your API key and preferences:

```bash
code-tutor setup
```

You'll be prompted to provide:
- Your Anthropic API key
- Your preferred Claude model (Sonnet 4.5 or Haiku 4.5)
- Your programming experience level (beginner/intermediate/advanced/expert)
- Your preferred question style (socratic/direct/exploratory)
- Focus areas for feedback (design, readability, performance, etc.)

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

### 3. Interactive Session

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
  "api_key": "your-api-key",
  "model": "claude-sonnet-4-5",
  "experience_level": "intermediate",
  "preferences": {
    "question_style": "socratic",
    "verbosity": "medium",
    "focus_areas": ["design", "readability"]
  }
}
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

Choose which Claude model to use for code review:
- **claude-sonnet-4-5** (default): Balanced performance and capability
- **claude-haiku-4-5**: Fastest and most cost-effective option

### Focus Areas

Choose what matters most to you:
- **Design**: Architecture and design patterns
- **Readability**: Code clarity and maintainability
- **Performance**: Efficiency and optimization
- **Security**: Security vulnerabilities and best practices
- **Testing**: Test coverage and quality
- **Documentation**: Comments and documentation

## Example Session

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
│       ├── cli.py           # Command-line interface
│       ├── config.py        # Configuration management
│       ├── file_reader.py   # File reading and parsing
│       ├── analyzer.py      # Code analysis with Claude API
│       └── session.py       # Interactive session management
├── tests/                   # Test files (coming soon)
├── DESIGN.md               # Detailed design documentation
├── plan.org                # Project planning and ideas
├── pyproject.toml          # Project configuration
└── README.md              # This file
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
# Run tests (coming soon)
pytest

# Format code
black src/

# Lint code
ruff check src/
```

## How It Works

1. **File Reading**: Code Tutor reads your source files and extracts metadata (language, size, structure)

2. **Initial Analysis**: Using Claude AI, it performs an initial analysis to understand:
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
