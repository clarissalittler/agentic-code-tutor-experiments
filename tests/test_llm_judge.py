"""LLM-as-Judge tests for evaluating response quality.

These tests use an LLM to evaluate the quality of code review
and teaching responses. They are expensive and should run
periodically (weekly) rather than on every commit.
"""

import pytest
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@dataclass
class EvaluationResult:
    """Result of an LLM evaluation."""
    relevance: int  # 1-5: Does response address the specific code?
    helpfulness: int  # 1-5: Would this help the learner improve?
    tone: int  # 1-5: Is it encouraging and educational?
    accuracy: int  # 1-5: Are technical suggestions correct?
    clarity: int  # 1-5: Is it well-organized?
    reasoning: str

    @property
    def weighted_score(self) -> float:
        """Calculate weighted overall score."""
        return (
            self.relevance * 0.25 +
            self.helpfulness * 0.25 +
            self.tone * 0.20 +
            self.accuracy * 0.20 +
            self.clarity * 0.10
        )

    @property
    def all_scores(self) -> dict:
        """Return all scores as a dictionary."""
        return {
            "relevance": self.relevance,
            "helpfulness": self.helpfulness,
            "tone": self.tone,
            "accuracy": self.accuracy,
            "clarity": self.clarity,
            "weighted_overall": self.weighted_score
        }


class LLMJudge:
    """Uses an LLM to evaluate response quality."""

    EVALUATION_PROMPT = '''You are evaluating an AI code tutor's response. Rate each dimension 1-5.

## Context
- Learner experience level: {experience_level}
- Code being reviewed:
```{language}
{code}
```

## AI Tutor's Response:
{response}

## Evaluation Rubric

**Relevance (1-5)**: Does the response specifically address this code?
- 1: Generic, could apply to any code
- 3: Somewhat specific but misses key aspects
- 5: Highly specific to this code's structure and patterns

**Helpfulness (1-5)**: Would this help the learner improve?
- 1: Not actionable or misleading
- 3: Some useful suggestions
- 5: Clear, actionable guidance with explanations

**Tone (1-5)**: Is it encouraging and educational (not critical)?
- 1: Harsh, condescending, or discouraging
- 3: Neutral but not particularly encouraging
- 5: Warm, supportive, assumes good intentions

**Accuracy (1-5)**: Are technical suggestions correct?
- 1: Contains errors or bad advice
- 3: Mostly correct with minor issues
- 5: Technically accurate and appropriate

**Clarity (1-5)**: Is it well-organized and easy to follow?
- 1: Confusing or poorly structured
- 3: Understandable but could be clearer
- 5: Crystal clear, well-formatted

Respond in JSON format only:
{{
  "relevance": <1-5>,
  "helpfulness": <1-5>,
  "tone": <1-5>,
  "accuracy": <1-5>,
  "clarity": <1-5>,
  "reasoning": "<brief explanation of scores>"
}}'''

    def __init__(self, api_key: str, model: str = "claude-haiku-4-5"):
        """Initialize with a fast/cheap model for evaluation."""
        import anthropic
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def evaluate(
        self,
        code: str,
        response: str,
        experience_level: str,
        language: str = "python"
    ) -> EvaluationResult:
        """
        Evaluate a code review response.

        Args:
            code: The code that was reviewed
            response: The tutor's response to evaluate
            experience_level: The learner's experience level
            language: Programming language

        Returns:
            EvaluationResult with scores and reasoning
        """
        prompt = self.EVALUATION_PROMPT.format(
            experience_level=experience_level,
            language=language,
            code=code,
            response=response
        )

        result = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )

        content = result.content[0].text

        # Handle potential markdown code blocks in response
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        try:
            data = json.loads(content.strip())
        except json.JSONDecodeError:
            # Fallback: try to extract values manually
            data = self._parse_fallback(content)

        return EvaluationResult(
            relevance=int(data.get("relevance", 3)),
            helpfulness=int(data.get("helpfulness", 3)),
            tone=int(data.get("tone", 3)),
            accuracy=int(data.get("accuracy", 3)),
            clarity=int(data.get("clarity", 3)),
            reasoning=data.get("reasoning", "No reasoning provided")
        )

    def _parse_fallback(self, content: str) -> dict:
        """Fallback parsing for malformed JSON."""
        result = {}
        for field in ["relevance", "helpfulness", "tone", "accuracy", "clarity"]:
            # Look for patterns like "relevance: 4" or "relevance": 4
            import re
            match = re.search(rf'{field}["\s:]+(\d)', content, re.IGNORECASE)
            if match:
                result[field] = int(match.group(1))
        return result


# Test fixtures and utilities
@pytest.fixture
def api_key():
    """Get API key, skip if not available."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        pytest.skip("ANTHROPIC_API_KEY not set")
    return key


@pytest.fixture
def judge(api_key):
    """Create an LLM judge instance."""
    return LLMJudge(api_key)


# Sample test cases
SAMPLE_CODE_REVIEWS = [
    {
        "code": '''def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
''',
        "response": '''## Questions

1. Have you considered what happens with large values of n?
2. What was your reasoning for using recursion here?

## Initial Observations

- The base case handling is correct
- The recursive structure follows the mathematical definition
- This implementation has exponential time complexity
''',
        "experience_level": "intermediate",
        "language": "python",
        "expected_min_scores": {
            "relevance": 3,
            "helpfulness": 3,
            "tone": 4,
            "accuracy": 4,
            "clarity": 4
        }
    },
    {
        "code": '''def quicksort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[0]
    less = [x for x in arr[1:] if x <= pivot]
    greater = [x for x in arr[1:] if x > pivot]
    return quicksort(less) + [pivot] + quicksort(greater)
''',
        "response": '''## Questions

1. Why did you choose the first element as the pivot?
2. How would this perform on already-sorted arrays?
3. Are there scenarios where the list comprehensions might be inefficient?

## Initial Observations

- Clean, readable implementation of quicksort
- List comprehensions make the logic clear
- First-element pivot could lead to worst-case O(n²) on sorted input
- Memory usage could be high due to creating new lists
''',
        "experience_level": "advanced",
        "language": "python",
        "expected_min_scores": {
            "relevance": 4,
            "helpfulness": 4,
            "tone": 4,
            "accuracy": 4,
            "clarity": 4
        }
    }
]


@pytest.mark.slow
class TestLLMJudge:
    """Tests using LLM-as-judge evaluation."""

    def test_judge_evaluates_response(self, judge):
        """Test that judge can evaluate a response."""
        case = SAMPLE_CODE_REVIEWS[0]

        result = judge.evaluate(
            code=case["code"],
            response=case["response"],
            experience_level=case["experience_level"],
            language=case["language"]
        )

        # Check all scores are in valid range
        assert 1 <= result.relevance <= 5
        assert 1 <= result.helpfulness <= 5
        assert 1 <= result.tone <= 5
        assert 1 <= result.accuracy <= 5
        assert 1 <= result.clarity <= 5
        assert result.reasoning  # Should have some reasoning

    @pytest.mark.parametrize("case", SAMPLE_CODE_REVIEWS)
    def test_good_responses_score_well(self, judge, case):
        """Test that our sample good responses score well."""
        result = judge.evaluate(
            code=case["code"],
            response=case["response"],
            experience_level=case["experience_level"],
            language=case["language"]
        )

        # Check against minimum expected scores
        for dimension, min_score in case["expected_min_scores"].items():
            actual = getattr(result, dimension)
            assert actual >= min_score, (
                f"{dimension} score {actual} below minimum {min_score}. "
                f"Reasoning: {result.reasoning}"
            )

    def test_harsh_response_scores_low_on_tone(self, judge):
        """Test that a harsh response scores low on tone."""
        harsh_response = '''## Questions

1. Why did you write such inefficient code?
2. Don't you know about memoization?

## Initial Observations

- This is a terrible implementation
- Any competent programmer would know to use dynamic programming
- The code is basically wrong for any practical use
'''

        result = judge.evaluate(
            code="def fib(n): return fib(n-1) + fib(n-2) if n > 1 else n",
            response=harsh_response,
            experience_level="beginner",
            language="python"
        )

        # Harsh tone should score low
        assert result.tone <= 2, f"Harsh response got tone score {result.tone}"

    def test_generic_response_scores_low_on_relevance(self, judge):
        """Test that a generic response scores low on relevance."""
        generic_response = '''## Questions

1. What are you trying to accomplish?
2. What are your requirements?

## Initial Observations

- Code looks structured
- Consider adding comments
- Think about edge cases
'''

        specific_code = '''def calculate_compound_interest(principal, rate, time, n):
    """Calculate compound interest with n compounding periods per year."""
    return principal * (1 + rate/n) ** (n * time)
'''

        result = judge.evaluate(
            code=specific_code,
            response=generic_response,
            experience_level="intermediate",
            language="python"
        )

        # Generic response that doesn't mention specific code elements
        assert result.relevance <= 3, f"Generic response got relevance score {result.relevance}"


@pytest.mark.slow
class TestLLMJudgeMetrics:
    """Track evaluation metrics over time."""

    def test_collect_metrics(self, judge, tmp_path):
        """Collect and save metrics from evaluation runs."""
        metrics_file = tmp_path / "judge_metrics.json"
        metrics = []

        for case in SAMPLE_CODE_REVIEWS:
            result = judge.evaluate(
                code=case["code"],
                response=case["response"],
                experience_level=case["experience_level"],
                language=case["language"]
            )

            metrics.append({
                "scores": result.all_scores,
                "experience_level": case["experience_level"]
            })

        # Save metrics
        with open(metrics_file, "w") as f:
            json.dump(metrics, f, indent=2)

        # Verify metrics were collected
        assert metrics_file.exists()
        with open(metrics_file) as f:
            saved = json.load(f)
        assert len(saved) == len(SAMPLE_CODE_REVIEWS)


# Utility for running evaluation outside of tests
def run_evaluation(api_key: str, code: str, response: str, experience_level: str):
    """Run a single evaluation and print results."""
    judge = LLMJudge(api_key)
    result = judge.evaluate(code, response, experience_level)

    print("\n=== Evaluation Results ===")
    print(f"Relevance:   {result.relevance}/5")
    print(f"Helpfulness: {result.helpfulness}/5")
    print(f"Tone:        {result.tone}/5")
    print(f"Accuracy:    {result.accuracy}/5")
    print(f"Clarity:     {result.clarity}/5")
    print(f"Overall:     {result.weighted_score:.2f}/5")
    print(f"\nReasoning: {result.reasoning}")

    return result


if __name__ == "__main__":
    # Example usage
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        run_evaluation(
            api_key,
            code="def add(a, b): return a + b",
            response="## Questions\n1. Why add?\n\n## Observations\n- Simple function",
            experience_level="beginner"
        )
    else:
        print("Set ANTHROPIC_API_KEY to run evaluation")
