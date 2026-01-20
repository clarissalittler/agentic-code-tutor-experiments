"""Contract tests to validate LLM response structure.

These tests verify that responses meet structural contracts,
regardless of specific content.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tests.contracts import (
    InitialAnalysisContract,
    ExerciseContract,
    FeedbackContract,
    TeachingResponseContract,
    ReviewSubmissionContract,
)
from code_tutor.analyzer import CodeAnalyzer
from code_tutor.exercise_generator import ExerciseGenerator


# Sample responses that represent various valid formats
VALID_ANALYSIS_RESPONSES = [
    # Standard format
    """## Questions

1. Why did you choose to use a dictionary here instead of a class?
2. What happens when the input is empty?
3. Have you considered the performance implications for large datasets?

## Initial Observations

- The code follows a clear functional style
- Error handling is comprehensive
- Good use of descriptive variable names
""",
    # Minimal valid response
    """## Questions

1. What's the intended use case for this code?

## Initial Observations

- Straightforward implementation
""",
    # Alternative header format
    """## Question

1. How do you handle null inputs?
2. What's the expected time complexity?

## Observations

- Clean separation of concerns
- Could benefit from documentation
- Uses modern language features
""",
    # More questions, fewer observations
    """## Questions

1. First question about design choices?
2. Second question about error handling?
3. Third question about testing strategy?
4. Fourth question about deployment?

## Initial Observations

- Well-structured code
""",
]

INVALID_ANALYSIS_RESPONSES = [
    # No questions
    """## Questions

## Initial Observations

- Just observations here
""",
    # No observations
    """## Questions

1. A question?

## Initial Observations

""",
    # Questions too short
    """## Questions

1. Q?
2. Why?

## Initial Observations

- Valid observation
""",
]


class TestInitialAnalysisContract:
    """Test the InitialAnalysisContract validator."""

    @pytest.fixture
    def contract(self):
        return InitialAnalysisContract()

    @pytest.fixture
    def analyzer(self):
        return CodeAnalyzer(api_key="fake", model="fake")

    @pytest.mark.parametrize("response", VALID_ANALYSIS_RESPONSES)
    def test_valid_responses_pass_contract(self, contract, analyzer, response):
        """Test that valid responses pass the contract."""
        result = analyzer._parse_initial_response(response)
        errors = contract.validate(result)

        assert not errors, f"Contract violations: {errors}"

    @pytest.mark.parametrize("response", INVALID_ANALYSIS_RESPONSES)
    def test_invalid_responses_fail_contract(self, contract, analyzer, response):
        """Test that invalid responses fail the contract."""
        result = analyzer._parse_initial_response(response)
        errors = contract.validate(result)

        # Should have at least one error
        assert errors, "Expected contract violation but none found"

    def test_question_count_bounds(self, contract, analyzer):
        """Test that question count bounds are enforced."""
        # Too many questions
        many_questions = "## Questions\n\n" + "\n".join(
            f"{i}. Question {i}?" for i in range(1, 10)
        ) + "\n\n## Initial Observations\n\n- One observation"

        result = analyzer._parse_initial_response(many_questions)
        errors = contract.validate(result)

        assert any("Too many questions" in e for e in errors)

    def test_custom_bounds(self, analyzer):
        """Test contract with custom bounds."""
        strict_contract = InitialAnalysisContract(
            min_questions=2,
            max_questions=3,
            min_observations=2,
            max_observations=4
        )

        response = """## Questions

1. Only one question?

## Initial Observations

- Only one observation
"""
        result = analyzer._parse_initial_response(response)
        errors = strict_contract.validate(result)

        assert any("Too few questions" in e for e in errors)
        assert any("Too few observations" in e for e in errors)


VALID_EXERCISE_RESPONSES = [
    """## Instructions

Write a function that implements binary search on a sorted array.
Your function should return the index of the target element, or -1 if not found.
Consider edge cases like empty arrays and arrays with a single element.

## Learning Objectives

- Understand the binary search algorithm
- Handle edge cases in search algorithms
- Analyze time complexity

## Starter Code
```python
def binary_search(arr: list, target: int) -> int:
    # TODO: Implement binary search
    pass
```

## Test Code
```python
assert binary_search([1, 2, 3, 4, 5], 3) == 2
assert binary_search([1, 2, 3], 4) == -1
assert binary_search([], 1) == -1
```

## Hints

1. Start with two pointers at the beginning and end of the array
2. Calculate the middle index and compare with the target
3. Narrow down the search space based on the comparison

## Solution Explanation

Binary search works by repeatedly dividing the search interval in half.
Compare the target with the middle element and eliminate half of the remaining elements.
""",
    # Minimal valid exercise
    """## Instructions

Implement a function to reverse a string. The function should not use built-in reverse methods.
This exercise helps understand string manipulation and iteration.

## Starter Code
```python
def reverse_string(s: str) -> str:
    pass
```

## Hints

1. Think about iterating from the end
2. You can build a new string character by character
""",
]

INVALID_EXERCISE_RESPONSES = [
    # Missing instructions
    """## Starter Code
```python
def something():
    pass
```

## Hints
1. A hint
2. Another hint
""",
    # Instructions too short
    """## Instructions

Do it.

## Starter Code
```python
def f():
    pass
```

## Hints
1. Think
2. Code
""",
    # Not enough hints
    """## Instructions

Write a comprehensive function to handle all edge cases in data processing.
Make sure to consider performance implications and error handling.

## Starter Code
```python
def process(data):
    pass
```

## Hints
1. Just one hint
""",
]


class TestExerciseContract:
    """Test the ExerciseContract validator."""

    @pytest.fixture
    def contract(self):
        return ExerciseContract()

    @pytest.fixture
    def generator(self):
        return ExerciseGenerator(api_key="fake", model="fake")

    @pytest.mark.parametrize("response", VALID_EXERCISE_RESPONSES)
    def test_valid_exercises_pass_contract(self, contract, generator, response):
        """Test that valid exercises pass the contract."""
        result = generator._parse_exercise_response(response)
        errors = contract.validate(result)

        assert not errors, f"Contract violations: {errors}"

    @pytest.mark.parametrize("response", INVALID_EXERCISE_RESPONSES)
    def test_invalid_exercises_fail_contract(self, contract, generator, response):
        """Test that invalid exercises fail the contract."""
        result = generator._parse_exercise_response(response)
        errors = contract.validate(result)

        assert errors, "Expected contract violation but none found"


class TestFeedbackContract:
    """Test the FeedbackContract validator."""

    @pytest.fixture
    def contract(self):
        return FeedbackContract()

    def test_substantive_feedback_passes(self, contract):
        """Test that substantive feedback passes."""
        result = {
            "feedback": """## Positive Feedback

Your implementation shows a good understanding of the problem. The variable naming
is clear and the logic flow is easy to follow.

## Suggestions for Improvement

Consider adding error handling for edge cases. You might also want to add
type hints to improve code documentation.

## Learning Opportunities

Look into Python's itertools module for more efficient iteration patterns.
"""
        }

        errors = contract.validate(result)
        assert not errors

    def test_short_feedback_fails(self, contract):
        """Test that very short feedback fails."""
        result = {"feedback": "Good job!"}

        errors = contract.validate(result)
        assert any("too short" in e.lower() for e in errors)


class TestTeachingResponseContract:
    """Test the TeachingResponseContract validator."""

    @pytest.fixture
    def contract(self):
        return TeachingResponseContract()

    def test_valid_teaching_response(self, contract):
        """Test a valid teaching response."""
        result = {
            "code": "def add(a, b):\n    return a - b  # Bug!",
            "issues": ["Using subtraction instead of addition"]
        }

        errors = contract.validate(result)
        assert not errors

    def test_missing_code(self, contract):
        """Test that missing code fails."""
        result = {
            "code": "",
            "issues": ["Some issue"]
        }

        errors = contract.validate(result)
        assert any("Code too short" in e for e in errors)

    def test_missing_issues(self, contract):
        """Test that missing issues fails."""
        result = {
            "code": "def example():\n    pass",
            "issues": []
        }

        errors = contract.validate(result)
        assert any("Too few issues" in e for e in errors)


class TestReviewSubmissionContract:
    """Test the ReviewSubmissionContract validator."""

    @pytest.fixture
    def contract(self):
        return ReviewSubmissionContract()

    def test_valid_review(self, contract):
        """Test a valid submission review."""
        result = {
            "feedback": """## Correctness

The solution correctly implements the required functionality.
All test cases pass.

## Code Quality

Good variable naming and structure.

## Overall Assessment
GOOD

Your solution demonstrates a solid understanding of the concepts.
""",
            "assessment": "GOOD"
        }

        errors = contract.validate(result)
        assert not errors

    @pytest.mark.parametrize("assessment", ["NEEDS_WORK", "ACCEPTABLE", "GOOD", "EXCELLENT"])
    def test_valid_assessments(self, contract, assessment):
        """Test all valid assessment values."""
        result = {
            "feedback": "A" * 200,  # Long enough feedback
            "assessment": assessment
        }

        errors = contract.validate(result)
        # Only check assessment-related errors
        assessment_errors = [e for e in errors if "assessment" in e.lower()]
        assert not assessment_errors

    def test_invalid_assessment(self, contract):
        """Test that invalid assessment fails."""
        result = {
            "feedback": "A" * 200,
            "assessment": "AMAZING"  # Not a valid value
        }

        errors = contract.validate(result)
        assert any("Invalid assessment" in e for e in errors)
