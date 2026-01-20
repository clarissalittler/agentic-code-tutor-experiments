"""Mock-based tests for CodeAnalyzer.

These tests use mocked API responses to test logic flow
without making actual API calls.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def create_mock_response(text: str):
    """Create a mock Anthropic API response."""
    mock_response = Mock()
    mock_content = Mock()
    mock_content.text = text
    mock_response.content = [mock_content]
    return mock_response


class TestCodeAnalyzerMocked:
    """Tests for CodeAnalyzer using mocked API calls."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock Anthropic client."""
        with patch('code_tutor.analyzer.anthropic.Anthropic') as mock_class:
            mock_instance = MagicMock()
            mock_class.return_value = mock_instance
            yield mock_instance

    def test_analyze_code_builds_correct_prompt(self, mock_client):
        """Verify prompt includes all necessary context."""
        from code_tutor.analyzer import CodeAnalyzer

        # Setup mock response
        mock_client.messages.create.return_value = create_mock_response(
            """## Questions

1. Test question?

## Initial Observations

- Test observation
"""
        )

        analyzer = CodeAnalyzer(api_key="test-key", model="claude-sonnet-4-5")

        result = analyzer.analyze_code(
            code="def hello(): pass",
            file_metadata={"language": "Python", "line_count": 1, "name": "test.py"},
            experience_level="intermediate",
            preferences={"focus_areas": ["design", "performance"], "question_style": "socratic"}
        )

        # Verify the call was made
        mock_client.messages.create.assert_called_once()
        call_kwargs = mock_client.messages.create.call_args.kwargs

        # Check model was passed
        assert call_kwargs["model"] == "claude-sonnet-4-5"

        # Check prompt contains expected elements
        prompt = call_kwargs["messages"][0]["content"]
        assert "intermediate" in prompt
        assert "Python" in prompt
        assert "def hello(): pass" in prompt
        assert "socratic" in prompt
        assert "design" in prompt

    def test_analyze_code_respects_experience_level(self, mock_client):
        """Verify experience level affects prompt content."""
        from code_tutor.analyzer import CodeAnalyzer

        mock_client.messages.create.return_value = create_mock_response(
            "## Questions\n1. Q?\n\n## Initial Observations\n- O"
        )

        analyzer = CodeAnalyzer(api_key="test-key", model="test-model")

        # Test beginner
        analyzer.analyze_code(
            code="x = 1",
            file_metadata={"language": "Python"},
            experience_level="beginner",
            preferences={}
        )

        beginner_prompt = mock_client.messages.create.call_args.kwargs["messages"][0]["content"]
        assert "learning" in beginner_prompt.lower() or "beginner" in beginner_prompt.lower()

        # Reset and test expert
        mock_client.messages.create.reset_mock()
        analyzer.reset_conversation()

        analyzer.analyze_code(
            code="x = 1",
            file_metadata={"language": "Python"},
            experience_level="expert",
            preferences={}
        )

        expert_prompt = mock_client.messages.create.call_args.kwargs["messages"][0]["content"]
        assert "expert" in expert_prompt.lower() or "skilled" in expert_prompt.lower()

    def test_conversation_history_maintained(self, mock_client):
        """Verify conversation history accumulates correctly."""
        from code_tutor.analyzer import CodeAnalyzer

        mock_client.messages.create.return_value = create_mock_response(
            "## Questions\n1. Q?\n\n## Initial Observations\n- O"
        )

        analyzer = CodeAnalyzer(api_key="test-key", model="test-model")

        # First call - analyze_code
        analyzer.analyze_code(
            code="test code",
            file_metadata={"language": "Python"},
            experience_level="beginner",
            preferences={}
        )

        assert len(analyzer.conversation_history) == 2  # user + assistant

        # Second call - process_answers
        mock_client.messages.create.return_value = create_mock_response("Feedback response")

        analyzer.process_answers(
            answers=["Answer 1", "Answer 2"],
            experience_level="beginner",
            preferences={}
        )

        assert len(analyzer.conversation_history) == 4  # 2 + 2 more

        # Third call - continue_conversation
        mock_client.messages.create.return_value = create_mock_response("Follow-up response")

        analyzer.continue_conversation("A follow-up question")

        assert len(analyzer.conversation_history) == 6

    def test_process_answers_includes_history(self, mock_client):
        """Verify process_answers sends full conversation history."""
        from code_tutor.analyzer import CodeAnalyzer

        mock_client.messages.create.return_value = create_mock_response(
            "## Questions\n1. Q?\n\n## Initial Observations\n- O"
        )

        analyzer = CodeAnalyzer(api_key="test-key", model="test-model")

        # First call
        analyzer.analyze_code(
            code="test code",
            file_metadata={"language": "Python"},
            experience_level="intermediate",
            preferences={}
        )

        # Second call
        mock_client.messages.create.return_value = create_mock_response("Feedback")

        analyzer.process_answers(
            answers=["My answer"],
            experience_level="intermediate",
            preferences={}
        )

        # Check that history was passed
        call_kwargs = mock_client.messages.create.call_args.kwargs
        messages = call_kwargs["messages"]

        # Should have multiple messages (conversation history)
        assert len(messages) >= 3  # Initial user, assistant, new user

    def test_reset_conversation_clears_history(self, mock_client):
        """Verify reset_conversation clears the history."""
        from code_tutor.analyzer import CodeAnalyzer

        mock_client.messages.create.return_value = create_mock_response(
            "## Questions\n1. Q?\n\n## Initial Observations\n- O"
        )

        analyzer = CodeAnalyzer(api_key="test-key", model="test-model")

        # Build up history
        analyzer.analyze_code(
            code="test",
            file_metadata={},
            experience_level="beginner",
            preferences={}
        )

        assert len(analyzer.conversation_history) > 0

        # Reset
        analyzer.reset_conversation()

        assert len(analyzer.conversation_history) == 0

    def test_error_handling_on_api_failure(self, mock_client):
        """Verify proper error handling when API fails."""
        from code_tutor.analyzer import CodeAnalyzer

        mock_client.messages.create.side_effect = Exception("API error")

        analyzer = CodeAnalyzer(api_key="test-key", model="test-model")

        with pytest.raises(ValueError) as exc_info:
            analyzer.analyze_code(
                code="test",
                file_metadata={},
                experience_level="beginner",
                preferences={}
            )

        assert "Failed to analyze code" in str(exc_info.value)

    def test_focus_areas_included_in_prompt(self, mock_client):
        """Verify focus areas are included in the prompt."""
        from code_tutor.analyzer import CodeAnalyzer

        mock_client.messages.create.return_value = create_mock_response(
            "## Questions\n1. Q?\n\n## Initial Observations\n- O"
        )

        analyzer = CodeAnalyzer(api_key="test-key", model="test-model")

        analyzer.analyze_code(
            code="test",
            file_metadata={"language": "Python"},
            experience_level="intermediate",
            preferences={
                "focus_areas": ["security", "performance", "testing"],
                "question_style": "direct"
            }
        )

        prompt = mock_client.messages.create.call_args.kwargs["messages"][0]["content"]

        assert "security" in prompt.lower()
        assert "performance" in prompt.lower()
        assert "testing" in prompt.lower()
        assert "direct" in prompt.lower()

    def test_file_metadata_included_in_prompt(self, mock_client):
        """Verify file metadata is included in the prompt."""
        from code_tutor.analyzer import CodeAnalyzer

        mock_client.messages.create.return_value = create_mock_response(
            "## Questions\n1. Q?\n\n## Initial Observations\n- O"
        )

        analyzer = CodeAnalyzer(api_key="test-key", model="test-model")

        analyzer.analyze_code(
            code="function test() {}",
            file_metadata={
                "language": "JavaScript",
                "line_count": 42,
                "name": "app.js"
            },
            experience_level="advanced",
            preferences={}
        )

        prompt = mock_client.messages.create.call_args.kwargs["messages"][0]["content"]

        assert "JavaScript" in prompt
        assert "42" in prompt
        assert "app.js" in prompt


class TestExerciseGeneratorMocked:
    """Tests for ExerciseGenerator using mocked API calls."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock Anthropic client."""
        with patch('code_tutor.exercise_generator.anthropic.Anthropic') as mock_class:
            mock_instance = MagicMock()
            mock_class.return_value = mock_instance
            yield mock_instance

    def test_generate_exercise_includes_topic(self, mock_client):
        """Verify topic is included in generation prompt."""
        from code_tutor.exercise_generator import ExerciseGenerator

        mock_client.messages.create.return_value = create_mock_response(
            """## Instructions
Implement binary search.

## Starter Code
```python
def binary_search(arr, target):
    pass
```

## Hints
1. Use two pointers
"""
        )

        generator = ExerciseGenerator(api_key="test-key", model="test-model")

        generator.generate_exercise(
            topic="binary search",
            language="Python",
            exercise_type="implementation",
            difficulty="intermediate",
            experience_level="intermediate"
        )

        prompt = mock_client.messages.create.call_args.kwargs["messages"][0]["content"]

        assert "binary search" in prompt.lower()
        assert "Python" in prompt
        assert "intermediate" in prompt.lower()

    def test_review_submission_includes_context(self, mock_client):
        """Verify review includes original exercise context."""
        from code_tutor.exercise_generator import ExerciseGenerator

        mock_client.messages.create.return_value = create_mock_response(
            """## Correctness
The solution is correct.

## Code Quality
Good structure.

## Overall Assessment
GOOD
"""
        )

        generator = ExerciseGenerator(api_key="test-key", model="test-model")

        generator.review_submission(
            original_exercise={
                "topic": "sorting",
                "exercise_type": "implementation",
                "learning_objectives": ["Understand quicksort", "Handle edge cases"]
            },
            submitted_code="def quicksort(arr): return sorted(arr)",
            language="Python",
            experience_level="beginner"
        )

        prompt = mock_client.messages.create.call_args.kwargs["messages"][0]["content"]

        assert "sorting" in prompt.lower()
        assert "beginner" in prompt.lower()
        assert "quicksort" in prompt.lower()
