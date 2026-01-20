"""Integration tests with real API calls.

These tests make actual API calls and should be run sparingly
(e.g., before releases or on merge to main).

Set ANTHROPIC_API_KEY environment variable to run these tests.
"""

import pytest
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tests.contracts import (
    InitialAnalysisContract,
    ExerciseContract,
    FeedbackContract,
)


# Skip all tests if no API key
pytestmark = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set"
)


@pytest.fixture
def api_key():
    """Get the API key."""
    return os.environ["ANTHROPIC_API_KEY"]


class TestCodeReviewIntegration:
    """Integration tests for the code review flow."""

    def test_analyze_code_returns_valid_structure(self, api_key):
        """Test that analyze_code returns properly structured response."""
        from code_tutor.analyzer import CodeAnalyzer

        # Use haiku for faster/cheaper integration tests
        analyzer = CodeAnalyzer(api_key=api_key, model="claude-haiku-4-5")

        code = '''def quicksort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + middle + quicksort(right)
'''

        result = analyzer.analyze_code(
            code=code,
            file_metadata={
                "language": "Python",
                "line_count": 9,
                "name": "sort.py"
            },
            experience_level="intermediate",
            preferences={
                "focus_areas": ["performance", "design"],
                "question_style": "socratic"
            }
        )

        # Validate structure
        contract = InitialAnalysisContract()
        errors = contract.validate(result)
        assert not errors, f"Contract violations: {errors}"

        # Verify questions are relevant to the code
        all_questions = " ".join(result["questions"]).lower()
        # At least one question should mention something related to sorting/code
        relevant_terms = ["pivot", "sort", "array", "recursion", "list", "element", "performance"]
        has_relevant = any(term in all_questions for term in relevant_terms)
        assert has_relevant, f"Questions don't seem relevant to the code: {result['questions']}"

    def test_complete_review_flow(self, api_key):
        """Test complete flow: analyze -> answer -> feedback."""
        from code_tutor.analyzer import CodeAnalyzer

        analyzer = CodeAnalyzer(api_key=api_key, model="claude-haiku-4-5")

        code = '''def is_palindrome(s):
    """Check if string is a palindrome."""
    s = s.lower().replace(" ", "")
    return s == s[::-1]
'''

        # Step 1: Initial analysis
        result = analyzer.analyze_code(
            code=code,
            file_metadata={"language": "Python", "line_count": 4, "name": "utils.py"},
            experience_level="beginner",
            preferences={"focus_areas": ["readability"], "question_style": "direct"}
        )

        assert result["questions"], "Should have questions"

        # Step 2: Process answers
        answers = [
            "I wanted a simple solution that's easy to understand",
            "I'm not worried about performance for this use case"
        ]

        feedback = analyzer.process_answers(
            answers=answers,
            experience_level="beginner",
            preferences={"focus_areas": ["readability"]}
        )

        # Validate feedback
        feedback_contract = FeedbackContract()
        errors = feedback_contract.validate(feedback)
        assert not errors, f"Feedback contract violations: {errors}"

    def test_follow_up_conversation(self, api_key):
        """Test follow-up conversation maintains context."""
        from code_tutor.analyzer import CodeAnalyzer

        analyzer = CodeAnalyzer(api_key=api_key, model="claude-haiku-4-5")

        # Initial analysis
        analyzer.analyze_code(
            code="def add(a, b): return a + b",
            file_metadata={"language": "Python"},
            experience_level="beginner",
            preferences={}
        )

        # Process some answers
        analyzer.process_answers(
            answers=["It's a simple addition function"],
            experience_level="beginner",
            preferences={}
        )

        # Follow-up
        response = analyzer.continue_conversation(
            "What about type hints? Should I add them?"
        )

        # Response should be relevant to type hints
        assert response
        assert len(response) > 50  # Should be substantive
        # Check for type-related terms
        response_lower = response.lower()
        type_terms = ["type", "hint", "annotation", "int", "float", "str"]
        assert any(term in response_lower for term in type_terms), (
            f"Follow-up about type hints got unrelated response: {response[:200]}..."
        )


class TestExerciseGenerationIntegration:
    """Integration tests for exercise generation."""

    def test_generate_exercise(self, api_key):
        """Test generating an exercise."""
        from code_tutor.exercise_generator import ExerciseGenerator

        generator = ExerciseGenerator(api_key=api_key, model="claude-haiku-4-5")

        exercise = generator.generate_exercise(
            topic="binary search",
            language="Python",
            exercise_type="implementation",
            difficulty="intermediate",
            experience_level="intermediate"
        )

        # Validate structure
        contract = ExerciseContract()
        errors = contract.validate(exercise)
        assert not errors, f"Contract violations: {errors}"

        # Check content relevance
        instructions = exercise.get("instructions", "").lower()
        assert "search" in instructions or "binary" in instructions, (
            f"Instructions don't mention binary search: {exercise['instructions'][:200]}"
        )

    def test_review_submission(self, api_key):
        """Test reviewing a submitted solution."""
        from code_tutor.exercise_generator import ExerciseGenerator

        generator = ExerciseGenerator(api_key=api_key, model="claude-haiku-4-5")

        submission = '''def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1
'''

        review = generator.review_submission(
            original_exercise={
                "topic": "binary search",
                "exercise_type": "implementation",
                "learning_objectives": ["Understand binary search algorithm"]
            },
            submitted_code=submission,
            language="Python",
            experience_level="intermediate"
        )

        assert "feedback" in review
        assert review["assessment"] in ["NEEDS_WORK", "ACCEPTABLE", "GOOD", "EXCELLENT"]

        # Good binary search implementation should get decent assessment
        assert review["assessment"] in ["ACCEPTABLE", "GOOD", "EXCELLENT"], (
            f"Good implementation got poor assessment: {review['assessment']}"
        )


class TestConfigIntegration:
    """Test configuration with real API calls."""

    def test_model_selection(self, api_key):
        """Test that different models can be used."""
        from code_tutor.analyzer import CodeAnalyzer

        # Test with different models (all should work)
        for model in ["claude-haiku-4-5"]:  # Only test haiku to save costs
            analyzer = CodeAnalyzer(api_key=api_key, model=model)

            result = analyzer.analyze_code(
                code="x = 1",
                file_metadata={"language": "Python"},
                experience_level="beginner",
                preferences={}
            )

            assert result["questions"] or result["observations"], (
                f"Model {model} returned empty result"
            )


class TestExperienceLevelAdaptation:
    """Test that responses adapt to experience level."""

    @pytest.mark.parametrize("level", ["beginner", "expert"])
    def test_experience_level_affects_response(self, api_key, level):
        """Test that different experience levels get appropriate responses."""
        from code_tutor.analyzer import CodeAnalyzer

        analyzer = CodeAnalyzer(api_key=api_key, model="claude-haiku-4-5")

        # Same code, different experience levels
        code = '''class Singleton:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
'''

        result = analyzer.analyze_code(
            code=code,
            file_metadata={"language": "Python", "name": "patterns.py"},
            experience_level=level,
            preferences={"focus_areas": ["design"]}
        )

        # Both should have questions
        assert result["questions"]

        # Response should have raw_response
        response = result["raw_response"].lower()

        if level == "beginner":
            # Beginner response might explain more
            # Just verify it doesn't use unexplained jargon excessively
            pass  # Hard to test without specific criteria

        elif level == "expert":
            # Expert response might use more technical terms
            pass  # Hard to test without specific criteria

        # At minimum, both should produce valid responses
        contract = InitialAnalysisContract()
        errors = contract.validate(result)
        assert not errors, f"Contract violations for {level}: {errors}"


class TestErrorHandling:
    """Test error handling in integration scenarios."""

    def test_invalid_api_key(self):
        """Test handling of invalid API key."""
        from code_tutor.analyzer import CodeAnalyzer

        analyzer = CodeAnalyzer(api_key="invalid-key", model="claude-haiku-4-5")

        with pytest.raises(ValueError) as exc_info:
            analyzer.analyze_code(
                code="x = 1",
                file_metadata={},
                experience_level="beginner",
                preferences={}
            )

        assert "Failed to analyze code" in str(exc_info.value)
