"""Golden sample tests using fuzzy matching.

These tests compare LLM outputs against known-good examples
using keyword matching and structural validation rather than
exact string comparison.
"""

import pytest
import json
import sys
from pathlib import Path
from difflib import SequenceMatcher
from typing import Dict, List, Any

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

GOLDEN_SAMPLES_DIR = Path(__file__).parent / "golden_samples"


def load_golden_sample(category: str, sample_id: str) -> tuple:
    """Load a golden sample input/expected pair."""
    sample_dir = GOLDEN_SAMPLES_DIR / category / sample_id

    with open(sample_dir / "input.json") as f:
        input_data = json.load(f)
    with open(sample_dir / "expected.json") as f:
        expected = json.load(f)

    return input_data, expected


def keyword_coverage(response: str, keywords: List[str]) -> float:
    """Calculate what percentage of expected keywords appear in response."""
    if not keywords:
        return 1.0

    response_lower = response.lower()
    matches = sum(1 for kw in keywords if kw.lower() in response_lower)
    return matches / len(keywords)


def check_anti_patterns(response: str, anti_patterns: List[str]) -> List[str]:
    """Check for anti-patterns that should NOT appear in response."""
    found = []
    response_lower = response.lower()

    for pattern in anti_patterns:
        if pattern.lower() in response_lower:
            found.append(pattern)

    return found


def check_sections(response: str, expected_sections: List[str]) -> List[str]:
    """Check for expected sections in response."""
    missing = []
    response_lower = response.lower()

    for section in expected_sections:
        # Check for section header (## Section or # Section)
        if section.lower() not in response_lower:
            missing.append(section)

    return missing


class GoldenSampleValidator:
    """Validate responses against golden sample expectations."""

    def __init__(
        self,
        keyword_threshold: float = 0.4,
        allow_anti_patterns: bool = False
    ):
        self.keyword_threshold = keyword_threshold
        self.allow_anti_patterns = allow_anti_patterns

    def validate(
        self,
        response: str,
        expected: Dict[str, Any],
        parsed_result: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Validate a response against expected golden sample.

        Args:
            response: The raw LLM response text
            expected: Expected validation criteria
            parsed_result: Optionally, the parsed result dict

        Returns:
            Dict with 'passed', 'issues', and 'metrics'
        """
        result = {
            "passed": True,
            "issues": [],
            "metrics": {}
        }

        # Check keyword coverage
        keywords = expected.get("keywords", [])
        if keywords:
            coverage = keyword_coverage(response, keywords)
            result["metrics"]["keyword_coverage"] = coverage

            if coverage < self.keyword_threshold:
                result["passed"] = False
                result["issues"].append(
                    f"Keyword coverage {coverage:.1%} below threshold {self.keyword_threshold:.1%}. "
                    f"Missing: {[k for k in keywords if k.lower() not in response.lower()]}"
                )

        # Check for anti-patterns
        anti_patterns = expected.get("anti_patterns", [])
        if anti_patterns and not self.allow_anti_patterns:
            found = check_anti_patterns(response, anti_patterns)
            if found:
                result["passed"] = False
                result["issues"].append(f"Found anti-patterns: {found}")

        # Check expected sections
        expected_sections = expected.get("expected_sections", [])
        if expected_sections:
            missing = check_sections(response, expected_sections)
            if missing:
                result["passed"] = False
                result["issues"].append(f"Missing sections: {missing}")

        # Check question count if parsed result provided
        if parsed_result:
            questions = parsed_result.get("questions", [])
            min_q = expected.get("min_questions", 1)
            max_q = expected.get("max_questions", 5)

            result["metrics"]["question_count"] = len(questions)

            if len(questions) < min_q:
                result["passed"] = False
                result["issues"].append(
                    f"Too few questions: {len(questions)} < {min_q}"
                )
            if len(questions) > max_q:
                result["passed"] = False
                result["issues"].append(
                    f"Too many questions: {len(questions)} > {max_q}"
                )

        return result


class TestGoldenSamples:
    """Test against golden samples (without making API calls)."""

    @pytest.fixture
    def validator(self):
        return GoldenSampleValidator(keyword_threshold=0.4)

    def test_load_golden_sample(self):
        """Test that golden samples can be loaded."""
        input_data, expected = load_golden_sample("code_review", "sample_001")

        assert "code" in input_data
        assert "keywords" in expected
        assert "fibonacci" in input_data["code"]

    def test_validator_with_good_response(self, validator):
        """Test validator passes a good response."""
        _, expected = load_golden_sample("code_review", "sample_001")

        # Simulate a good response
        good_response = """## Questions

1. Have you considered the time complexity implications of this recursive approach?
   The current implementation has exponential time complexity.
2. Would memoization be beneficial here to cache intermediate results?
3. What's your reasoning for the base case handling?

## Initial Observations

- Clean recursive implementation following the mathematical definition
- Good error handling for invalid input
- The recursion uses a proper base case
- Performance could be a concern for large n values
"""

        from code_tutor.analyzer import CodeAnalyzer
        analyzer = CodeAnalyzer(api_key="fake", model="fake")
        parsed = analyzer._parse_initial_response(good_response)

        result = validator.validate(good_response, expected, parsed)

        assert result["passed"], f"Expected pass but got issues: {result['issues']}"
        assert result["metrics"]["keyword_coverage"] >= 0.4

    def test_validator_catches_anti_patterns(self, validator):
        """Test validator catches anti-patterns."""
        _, expected = load_golden_sample("code_review", "sample_001")

        # Response with anti-patterns
        bad_response = """## Questions

1. Why did you write such terrible code?
2. This is obviously wrong, don't you know better?

## Initial Observations

- This is bad code overall
"""

        result = validator.validate(bad_response, expected)

        assert not result["passed"]
        assert any("anti-pattern" in issue.lower() for issue in result["issues"])

    def test_validator_catches_missing_sections(self, validator):
        """Test validator catches missing sections."""
        _, expected = load_golden_sample("code_review", "sample_001")

        # Response completely missing the observations section (no mention at all)
        incomplete_response = """## Questions

1. Why use recursion here?
2. What about memoization?

## Summary

This code looks fine.
"""

        result = validator.validate(incomplete_response, expected)

        assert not result["passed"]
        assert any("Missing sections" in issue for issue in result["issues"])

    def test_keyword_coverage_calculation(self):
        """Test keyword coverage calculation."""
        keywords = ["recursion", "performance", "memoization", "time complexity"]

        text_all = "This code uses recursion and has performance issues. Consider memoization to improve time complexity."
        assert keyword_coverage(text_all, keywords) == 1.0

        text_some = "This code uses recursion and has performance issues."
        assert keyword_coverage(text_some, keywords) == 0.5

        text_none = "This code is fine."
        assert keyword_coverage(text_none, keywords) == 0.0

    def test_check_anti_patterns(self):
        """Test anti-pattern detection."""
        anti_patterns = ["terrible", "stupid", "wrong"]

        clean_text = "Your code looks good with room for improvement."
        assert check_anti_patterns(clean_text, anti_patterns) == []

        bad_text = "This is terrible and wrong."
        found = check_anti_patterns(bad_text, anti_patterns)
        assert "terrible" in found
        assert "wrong" in found


class TestGoldenSampleValidation:
    """
    Tests that would run against real API responses.

    These are marked to skip unless explicitly enabled, as they require
    recorded responses or API access.
    """

    @pytest.mark.skip(reason="Requires recorded responses")
    def test_recorded_response_meets_expectations(self):
        """Test a recorded API response against expectations."""
        # This would load a recorded response and validate it
        pass


# Parametrized test for all golden samples
def get_all_golden_samples():
    """Discover all golden samples for parametrized testing."""
    samples = []
    for category_dir in GOLDEN_SAMPLES_DIR.iterdir():
        if category_dir.is_dir():
            for sample_dir in category_dir.iterdir():
                if sample_dir.is_dir() and (sample_dir / "input.json").exists():
                    samples.append((category_dir.name, sample_dir.name))
    return samples


@pytest.mark.parametrize("category,sample_id", get_all_golden_samples())
def test_golden_sample_files_valid(category, sample_id):
    """Ensure all golden sample files are valid JSON."""
    input_data, expected = load_golden_sample(category, sample_id)

    # Basic validation
    assert isinstance(input_data, dict)
    assert isinstance(expected, dict)

    # Input should have required fields
    if category == "code_review":
        assert "code" in input_data
        assert "file_metadata" in input_data

    # Expected should have validation criteria
    assert "keywords" in expected or "expected_sections" in expected
