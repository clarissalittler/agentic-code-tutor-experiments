# Code Tutor - Design Document

## Overview
A command-line tool that provides personalized code review and tutoring by analyzing code files and engaging in interactive dialogue with the programmer.

## Core Principles
1. **Respectful**: Understand and respect the programmer's style and intentions
2. **Educational**: Ask clarifying questions to understand design decisions
3. **Adaptive**: Tailor feedback to the programmer's experience level
4. **Interactive**: Engage in dialogue rather than one-way criticism

## Architecture

### Technology Stack
- **Language**: Python 3.9+
- **CLI Framework**: Click (for argument parsing and interactive prompts)
- **LLM API**: Anthropic Claude API (for intelligent code analysis)
- **Configuration**: JSON-based config file
- **File Storage**: `~/.config/code-tutor/` for configuration

### Core Components

#### 1. Configuration Manager (`config.py`)
- Manages user configuration (API key, experience level, preferences)
- First-time setup wizard
- Config file location: `~/.config/code-tutor/config.json`
- Config structure:
  ```json
  {
    "api_key": "sk-ant-...",
    "experience_level": "intermediate",
    "preferences": {
      "question_style": "socratic",
      "verbosity": "medium",
      "focus_areas": ["design", "readability", "performance"]
    }
  }
  ```

#### 2. File Reader (`file_reader.py`)
- Reads source code files
- Supports multiple file formats
- Handles encoding detection
- Provides file metadata (language, size, line count)

#### 3. Code Analyzer (`analyzer.py`)
- Interfaces with Claude API
- Generates context-aware prompts
- Parses API responses
- Maintains conversation history for follow-up questions

#### 4. Interactive Session (`session.py`)
- Manages the interactive review session
- Handles question-answer flow
- Tracks user responses
- Adapts follow-up questions based on answers

#### 5. CLI Interface (`cli.py`)
- Entry point for the application
- Command structure:
  - `code-tutor setup` - Initial configuration
  - `code-tutor review <file>` - Review a single file
  - `code-tutor review <dir>` - Review multiple files
  - `code-tutor config` - Update configuration
  - `code-tutor chat` - Continue conversation about last review

### User Flow

#### First-Time Setup
1. User runs `code-tutor setup`
2. Tool prompts for:
   - Anthropic API key
   - Experience level (beginner/intermediate/advanced/expert)
   - Preferred focus areas
3. Configuration saved to `~/.config/code-tutor/config.json`

#### Code Review Session
1. User runs `code-tutor review path/to/file.py`
2. Tool reads and analyzes the file
3. Initial analysis phase:
   - Identify language and frameworks
   - Understand overall structure
   - Note potential areas of interest
4. Interactive questioning phase:
   - Ask about design decisions
   - Understand intended use cases
   - Clarify ambiguous sections
5. Feedback phase:
   - Provide respectful, educational feedback
   - Suggest improvements aligned with user's style
   - Explain reasoning behind suggestions
6. Follow-up phase:
   - Allow user to ask questions
   - Dive deeper into specific topics

### LLM Prompting Strategy

The system will use a sophisticated prompt that:
1. **Sets the tone**: Respectful tutor, not a critic
2. **Provides context**: User's experience level, preferences
3. **Includes code**: The actual code being reviewed
4. **Guides behavior**: Ask before assuming, respect existing patterns
5. **Structures output**: Separate questions from feedback

Example prompt structure:
```
You are a respectful code tutor helping a [experience_level] programmer.
Your goal is to understand their code before critiquing it.

Programmer's preferences:
- Focus areas: [focus_areas]
- Question style: [question_style]

Code to review:
[code]

First, ask 2-3 thoughtful questions about:
1. Design decisions and rationale
2. Intended use cases or constraints
3. Any patterns that seem intentional

Format your response as:
## Questions
1. ...
2. ...

## Initial Observations
- ...
```

## Experience Level Adaptations

### Beginner
- More explanatory questions
- Focus on fundamentals
- Provide examples and references
- Avoid jargon

### Intermediate
- Balance between explanation and challenge
- Discuss trade-offs
- Introduce advanced concepts gradually

### Advanced/Expert
- Assume knowledge of patterns
- Focus on architecture and design
- Discuss performance implications
- Reference best practices critically

## Configuration Options

### Experience Levels
- `beginner`: 0-1 years programming
- `intermediate`: 1-3 years programming
- `advanced`: 3-5 years programming
- `expert`: 5+ years programming

### Question Styles
- `socratic`: Lead learner to answers through questions
- `direct`: Ask straightforward clarifying questions
- `exploratory`: Open-ended questions about alternatives

### Focus Areas
- `design`: Architecture and design patterns
- `readability`: Code clarity and maintainability
- `performance`: Efficiency and optimization
- `security`: Security vulnerabilities
- `testing`: Test coverage and quality
- `documentation`: Comments and docs

## Future Enhancements
- Support for project-wide analysis
- Integration with git for reviewing changes
- Save and replay review sessions
- Multiple LLM backend support
- Team configuration sharing
- Custom rule sets
