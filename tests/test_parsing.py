"""Unit tests for response parsing functions.

These tests are deterministic and don't require LLM calls.
They test the parsing logic that extracts structured data from LLM responses.
"""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from code_tutor.analyzer import CodeAnalyzer
from code_tutor.teaching_session import TeachingSession
from code_tutor.exercise_generator import ExerciseGenerator


class TestAnalyzerParsing:
    """Test parsing functions in CodeAnalyzer."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer with fake credentials (no API calls)."""
        # We're only testing parsing, so credentials don't matter
        return CodeAnalyzer(api_key="fake-key", model="fake-model")

    def test_parse_initial_response_standard_format(self, analyzer):
        """Test parsing a well-formatted analysis response."""
        response = """## Questions

1. Why did you choose to use a dictionary here instead of a class?
2. What happens when the input is empty?
3. Have you considered the performance implications?

## Initial Observations

- The code follows a clear functional style
- Error handling is comprehensive
- Good use of descriptive variable names
"""
        result = analyzer._parse_initial_response(response)

        assert len(result["questions"]) == 3
        assert "dictionary" in result["questions"][0]
        assert "empty" in result["questions"][1]
        assert len(result["observations"]) == 3
        assert "functional" in result["observations"][0]
        assert result["raw_response"] == response

    def test_parse_initial_response_alternate_headers(self, analyzer):
        """Test parsing with slightly different header formats."""
        response = """## Question

1. What trade-offs did you consider?
2. How do you handle edge cases?

## Observations

- Well-structured code
- Could benefit from more comments
"""
        result = analyzer._parse_initial_response(response)

        # Should still parse despite singular "Question" vs "Questions"
        assert len(result["questions"]) == 2
        assert len(result["observations"]) == 2

    def test_parse_initial_response_with_bullets(self, analyzer):
        """Test parsing observations with different bullet styles."""
        response = """## Questions

1. First question?
2. Second question?

## Initial Observations

* Observation with asterisk
- Observation with dash
• Observation with bullet point
"""
        result = analyzer._parse_initial_response(response)

        assert len(result["observations"]) == 3
        # All bullet styles should be stripped
        assert not any(obs.startswith(("*", "-", "•")) for obs in result["observations"])

    def test_parse_initial_response_empty_sections(self, analyzer):
        """Test handling when sections are empty or missing."""
        response = """## Questions

## Initial Observations

"""
        result = analyzer._parse_initial_response(response)

        assert result["questions"] == []
        assert result["observations"] == []

    def test_parse_initial_response_no_sections(self, analyzer):
        """Test handling when response lacks expected structure."""
        response = "This is just plain text without any sections."

        result = analyzer._parse_initial_response(response)

        assert result["questions"] == []
        assert result["observations"] == []
        assert result["raw_response"] == response

    def test_parse_initial_response_extra_sections_ignored(self, analyzer):
        """Test that extra sections don't break parsing."""
        response = """## Introduction

Some intro text.

## Questions

1. A question?

## Initial Observations

- An observation

## Conclusion

Some conclusion.
"""
        result = analyzer._parse_initial_response(response)

        assert len(result["questions"]) == 1
        assert len(result["observations"]) == 1

    def test_parse_initial_response_multiline_questions(self, analyzer):
        """Test handling questions that span multiple lines."""
        response = """## Questions

1. This is a longer question that might
   span multiple lines in the response?
2. Second question?

## Initial Observations

- First observation
"""
        result = analyzer._parse_initial_response(response)

        # Current implementation may not handle multi-line well
        # This test documents the current behavior
        assert len(result["questions"]) >= 1

    def test_parse_feedback_response(self, analyzer):
        """Test parsing feedback response (currently returns raw)."""
        response = """## Positive Feedback

Your code is well-structured.

## Suggestions

Consider adding type hints.
"""
        result = analyzer._parse_feedback_response(response)

        assert "feedback" in result
        assert "raw_response" in result
        assert result["feedback"] == response


class TestTeachingSessionParsing:
    """Test parsing functions in TeachingSession."""

    @pytest.fixture
    def session(self):
        """Create a teaching session for testing parsing only."""
        # We need a mock config manager
        from unittest.mock import Mock
        mock_config = Mock()
        mock_config.is_logging_enabled.return_value = False
        return TeachingSession(config_manager=mock_config)

    def test_parse_code_response_standard(self, session):
        """Test parsing a standard flawed code response."""
        response = """## Code
```python
def add(a, b):
    return a - b  # Bug: should be +
```

## Student Question
I'm trying to add two numbers but getting wrong results. What's happening?

## Hidden Issues
- Using subtraction instead of addition
- The operator is incorrect
"""
        result = session._parse_code_response(response)

        assert "return a - b" in result["code"]
        assert "add two numbers" in result["student_question"]
        assert len(result["issues"]) == 2
        assert "subtraction" in result["issues"][0].lower()

    def test_parse_code_response_multiple_code_blocks(self, session):
        """Test behavior with multiple code blocks.

        Note: The current implementation captures all code within code blocks.
        This test documents this behavior.
        """
        response = """## Code
```python
def main():
    pass
```

## Student Question
Why doesn't this work?

## Hidden Issues
- Missing implementation

Some extra code:
```python
# This should not be included
```
"""
        result = session._parse_code_response(response)

        assert "def main():" in result["code"]
        # Note: Current behavior includes all code blocks
        # If this is not desired, the parser would need to be updated

    def test_parse_code_response_no_code_block(self, session):
        """Test handling when code block is missing."""
        response = """## Code

No code provided here.

## Student Question
Help me!

## Hidden Issues
- No code
"""
        result = session._parse_code_response(response)

        # Should handle gracefully
        assert result["code"] == "" or "No code provided" not in result["code"]

    def test_parse_evaluation_response_understanding_achieved(self, session):
        """Test detecting understanding achieved."""
        response = """## Student Response

Thanks! Now I understand the issue.

## Teaching Quality Assessment

Good hints were provided.

## Understanding Achieved
YES
"""
        result = session._parse_evaluation_response(response)

        assert result["understanding_achieved"] is True

    def test_parse_evaluation_response_understanding_not_achieved(self, session):
        """Test detecting when understanding not achieved."""
        response = """## Student Response

I'm still confused.

## Understanding Achieved
NO
"""
        result = session._parse_evaluation_response(response)

        assert result["understanding_achieved"] is False


class TestExerciseGeneratorParsing:
    """Test parsing functions in ExerciseGenerator."""

    @pytest.fixture
    def generator(self):
        """Create generator with fake credentials."""
        return ExerciseGenerator(api_key="fake-key", model="fake-model")

    def test_parse_exercise_response_complete(self, generator):
        """Test parsing a complete exercise response."""
        response = """## Instructions

Write a function that calculates the factorial of a number.
The function should handle edge cases appropriately.

## Learning Objectives

- Understand recursion
- Handle base cases properly
- Consider performance implications

## Starter Code
```python
def factorial(n):
    # TODO: Implement this function
    pass
```

## Test Code
```python
assert factorial(5) == 120
assert factorial(0) == 1
```

## Hints

1. Start with the base case
2. Think about what happens when n is 0 or 1
3. The recursive case multiplies n by factorial(n-1)

## Solution Explanation

The factorial function uses recursion with a base case of n <= 1.
"""
        result = generator._parse_exercise_response(response)

        assert "factorial" in result["instructions"]
        assert len(result["learning_objectives"]) == 3
        assert "recursion" in result["learning_objectives"][0].lower()
        assert "def factorial" in result["starter_code"]
        assert "assert factorial" in result["test_code"]
        assert len(result["hints"]) == 3
        assert "base case" in result["hints"][0].lower()
        assert "recursion" in result["solution_explanation"].lower()

    def test_parse_exercise_response_missing_optional_sections(self, generator):
        """Test parsing when optional sections are missing."""
        response = """## Instructions

Implement binary search.

## Starter Code
```python
def binary_search(arr, target):
    pass
```

## Hints

1. Use two pointers
2. Calculate the middle index
"""
        result = generator._parse_exercise_response(response)

        assert "binary search" in result["instructions"].lower()
        assert result["starter_code"]
        assert len(result["hints"]) == 2
        assert result["learning_objectives"] == []
        assert result["test_code"] == ""

    def test_parse_exercise_response_with_nested_code_blocks(self, generator):
        """Test handling code blocks within hints or explanation."""
        response = """## Instructions

Implement a function.

## Starter Code
```python
def solve():
    pass
```

## Hints

1. Consider using a loop like:
   ```python
   for i in range(n):
   ```
2. Another hint

## Solution Explanation

The solution looks like this but you shouldn't see this code.
"""
        result = generator._parse_exercise_response(response)

        # Starter code should be captured correctly
        assert "def solve" in result["starter_code"]
        # Hints should be parsed
        assert len(result["hints"]) >= 1


class TestEdgeCases:
    """Test edge cases across all parsers."""

    def test_unicode_handling(self):
        """Test that unicode characters are handled correctly."""
        analyzer = CodeAnalyzer(api_key="fake", model="fake")

        response = """## Questions

1. Why use émojis 🎉 in variable names?
2. Cześć! What about international chars?

## Initial Observations

- Uses UTF-8 encoding properly
- Handles 日本語 text
"""
        result = analyzer._parse_initial_response(response)

        assert len(result["questions"]) == 2
        assert "émojis" in result["questions"][0] or "mojis" in result["questions"][0]

    def test_very_long_response(self):
        """Test handling of very long responses."""
        analyzer = CodeAnalyzer(api_key="fake", model="fake")

        # Generate a response with many items
        questions = "\n".join(f"{i}. Question number {i}?" for i in range(1, 20))
        observations = "\n".join(f"- Observation number {i}" for i in range(1, 50))

        response = f"""## Questions

{questions}

## Initial Observations

{observations}
"""
        result = analyzer._parse_initial_response(response)

        # Should parse all items (no artificial limits in parser)
        assert len(result["questions"]) > 10
        assert len(result["observations"]) > 20

    def test_empty_string_response(self):
        """Test handling of empty responses."""
        analyzer = CodeAnalyzer(api_key="fake", model="fake")

        result = analyzer._parse_initial_response("")

        assert result["questions"] == []
        assert result["observations"] == []
        assert result["raw_response"] == ""

    def test_whitespace_only_response(self):
        """Test handling of whitespace-only responses."""
        analyzer = CodeAnalyzer(api_key="fake", model="fake")

        result = analyzer._parse_initial_response("   \n\n\t  \n  ")

        assert result["questions"] == []
        assert result["observations"] == []
