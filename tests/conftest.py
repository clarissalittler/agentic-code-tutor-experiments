"""Pytest configuration and shared fixtures for Code Tutor tests."""

import pytest
import json
import os
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch
from typing import Optional


# Test data directory
TEST_DATA_DIR = Path(__file__).parent / "golden_samples"


class ResponseRecorder:
    """Record LLM responses for golden sample corpus."""

    def __init__(self, recordings_dir: Path):
        self.recordings_dir = recordings_dir
        self.recordings_dir.mkdir(parents=True, exist_ok=True)

    def record(self, category: str, input_data: dict, response: str, metadata: dict = None):
        """Record a response for potential use as golden sample."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{category}_{timestamp}.json"

        record = {
            "input": input_data,
            "response": response,
            "metadata": metadata or {},
            "recorded_at": datetime.now().isoformat()
        }

        with open(self.recordings_dir / filename, 'w') as f:
            json.dump(record, f, indent=2)


@pytest.fixture
def response_recorder(tmp_path):
    """Fixture for recording responses during tests."""
    return ResponseRecorder(tmp_path / "recordings")


@pytest.fixture
def mock_anthropic_client():
    """Create a mock Anthropic client for testing without API calls."""
    with patch('anthropic.Anthropic') as mock_class:
        mock_client = Mock()
        mock_class.return_value = mock_client
        yield mock_client


def create_mock_response(text: str):
    """Create a mock Anthropic API response."""
    mock_response = Mock()
    mock_content = Mock()
    mock_content.text = text
    mock_response.content = [mock_content]
    return mock_response


@pytest.fixture
def mock_analysis_response():
    """Return a standard mock analysis response."""
    return create_mock_response("""## Questions

1. Why did you choose to use a dictionary here instead of a class?
2. What happens when the input is empty?
3. Have you considered the performance implications for large datasets?

## Initial Observations

- The code follows a clear functional style
- Error handling is comprehensive
- Good use of descriptive variable names
""")


@pytest.fixture
def mock_feedback_response():
    """Return a standard mock feedback response."""
    return create_mock_response("""## Positive Feedback

Your approach to error handling is solid. The use of early returns keeps the code clean and readable.

## Suggestions for Improvement

1. Consider adding type hints to improve code clarity
2. The dictionary comprehension on line 15 could be simplified

## Learning Opportunities

- Look into dataclasses as an alternative to dictionaries
- Explore Python's typing module for better documentation

## Trade-offs Discussion

Your choice of a dictionary over a class trades flexibility for type safety.
""")


@pytest.fixture
def sample_python_code():
    """Return sample Python code for testing."""
    return '''def fibonacci(n):
    """Calculate the nth Fibonacci number."""
    if n <= 0:
        raise ValueError("n must be positive")
    if n <= 2:
        return 1
    return fibonacci(n - 1) + fibonacci(n - 2)


def factorial(n):
    """Calculate n factorial."""
    if n < 0:
        raise ValueError("n must be non-negative")
    if n <= 1:
        return 1
    return n * factorial(n - 1)
'''


@pytest.fixture
def sample_file_metadata():
    """Return sample file metadata for testing."""
    return {
        "name": "math_utils.py",
        "language": "Python",
        "line_count": 18,
        "size_bytes": 450,
        "non_empty_lines": 15
    }


@pytest.fixture
def sample_preferences():
    """Return sample user preferences for testing."""
    return {
        "focus_areas": ["design", "readability", "performance"],
        "question_style": "socratic"
    }


@pytest.fixture
def api_key():
    """Get API key from environment, skip test if not available."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        pytest.skip("ANTHROPIC_API_KEY not set")
    return key


# Markers for different test categories
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests (no external dependencies)")
    config.addinivalue_line("markers", "integration: Integration tests (requires API key)")
    config.addinivalue_line("markers", "slow: Slow tests (LLM-as-judge, etc.)")
    config.addinivalue_line("markers", "golden: Golden sample tests")
