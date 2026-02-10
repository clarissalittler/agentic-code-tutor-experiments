# Code Tutor - Design Document

## Overview
A command-line tool that provides three modes of learning:

1. **Code Review Mode**: Personalized code review by analyzing code files and engaging in interactive dialogue
2. **Teaching Mode (Teach Me!)**: Socratic learning through correcting intentionally flawed code
3. **Roguelike**: Generated homework problems on asked-for-topics that can be read and graded later by the tool

## Core Principles
1. **Respectful**: Understand and respect the programmer's style and intentions
2. **Educational**: Ask clarifying questions to understand design decisions
3. **Adaptive**: Tailor feedback to the programmer's experience level
4. **Interactive**: Engage in dialogue rather than one-way criticism
5. **Socratic**: Learn by teaching - identify and explain mistakes in code

## Architecture

### Technology Stack
- **Language**: Python 3.9+
- **CLI Framework**: Click (for argument parsing and interactive prompts)
- **LLM API**: Pluggable provider interface (Anthropic + OpenAI-compatible backends)
- **Configuration**: JSON-based config file
- **File Storage**: `~/.config/code-tutor/` for configuration

### Core Components

#### 1. Configuration Manager (`config.py`)
- Manages user configuration (API key, experience level, preferences)
- Normalizes loaded config to safe defaults (provider/model/preferences/logging)
- Exposes typed runtime provider settings via `LLMRuntimeConfig`
- Enforces explicit consent before unredacted logging is allowed
- First-time setup wizard
- Config file location: `~/.config/code-tutor/config.json`
- Config structure:
  ```json
  {
    "provider": "anthropic",
    "api_key": "sk-ant-...",
    "model": "claude-sonnet-4-5",
    "base_url": "",
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
- Interfaces with the configured LLM provider API
- Uses provider metadata (token usage) for API-call logging
- Generates context-aware prompts
- Parses API responses
- Maintains conversation history for follow-up questions

#### Provider Abstraction (`llm_provider.py`)
- Defines provider-agnostic `LLMClient` interface
- Implements Anthropic and OpenAI-compatible backends
- Normalizes provider aliases and instantiates backend clients
- Adds retry/backoff for transient OpenAI-compatible HTTP/network failures

#### Prompt Contracts (`contracts.py`)
- Defines workflow-specific prompt contracts as a single source of truth
- Co-locates JSON output schema instructions with parser/validation logic
- Provides resilient parsing fallbacks via shared response parsing helpers

#### Mode Services (`services.py`)
- Introduces a lightweight service layer for mode orchestration
- Moves non-trivial orchestration out of Click command handlers
- Keeps CLI focused on argument handling + user-facing rendering

#### 4. Interactive Session (`session.py`)
- Manages the interactive review session
- Handles question-answer flow
- Tracks user responses
- Adapts follow-up questions based on answers

#### 5. Teaching Session (`teaching_session.py`)
- Manages Socratic teaching mode (Teach Me!)
- Generates intentionally flawed code with clever mistakes
- Collects user's explanation of issues
- Evaluates understanding using the configured LLM provider
- Iteratively refines examples based on user's comprehension
- Tracks teaching rounds and progression

#### 6. CLI Interface (`cli.py`)
- Entry point for the application
- Command structure:
  - `code-tutor setup` - Initial configuration
  - `code-tutor review <file>` - Review a single file
  - `code-tutor review <dir>` - Review multiple files
  - `code-tutor teach-me` - Interactive teaching mode
  - `code-tutor roguelike <subcommand>` - Generate and grade persistent challenge runs
  - `code-tutor config` - Update configuration
  - `code-tutor info` - Show information

### User Flow

#### First-Time Setup
1. User runs `code-tutor setup`
2. Tool prompts for:
   - Provider selection (Anthropic or OpenAI-compatible)
   - Provider API key
   - Model selection/input
   - Optional base URL for OpenAI-compatible providers
   - Experience level (beginner/intermediate/advanced/expert)
   - Question style (socratic/direct/exploratory)
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

#### Teaching Session (Teach Me!)
1. User runs `code-tutor teach-me`
2. Topic selection:
   - User specifies what they want to learn (e.g., "recursion")
   - User selects programming language
3. Teaching rounds (iterative):
   - **Generate flawed code**: AI creates code with intentional, instructive mistakes
   - **Present code**: Display with syntax highlighting
   - **Collect explanation**: User explains what's wrong and why
   - **Evaluate understanding**: AI assesses explanation quality
   - **Provide feedback**: Constructive feedback on the explanation
   - **Decision point**:
     - If understanding achieved → Move to next concept or end
     - If needs refinement → Generate related example to deepen understanding
4. Conclusion:
   - Summary of learning progress
   - Encouragement to continue practicing

### LLM Prompting Strategy

The system uses contract-driven prompts that:
1. **Sets the tone**: Respectful tutor, not a critic
2. **Provides context**: User's experience level, preferences
3. **Includes code**: The actual code being reviewed
4. **Guides behavior**: Ask before assuming, respect existing patterns
5. **Structures output**: Requires strict JSON output schemas per workflow

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

### Available Models
- `claude-sonnet-4-5`: Balanced performance and capability (default)
- `claude-haiku-4-5`: Fastest and most cost-effective

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
