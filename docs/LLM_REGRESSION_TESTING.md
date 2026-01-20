# LLM Regression Testing Strategy for Code Tutor

Testing LLM-based applications presents unique challenges: outputs are non-deterministic, quality is subjective, and traditional assertions often don't apply. This document outlines a comprehensive testing strategy for the Code Tutor tool.

## Testing Philosophy

The goal isn't to test that the LLM produces *identical* outputs, but rather that it:
1. **Produces structurally valid outputs** (parseable, correct format)
2. **Maintains behavioral consistency** (similar inputs yield similar behaviors)
3. **Meets quality thresholds** (responses are helpful, appropriate, accurate)
4. **Respects constraints** (experience levels, focus areas, etc.)

## Testing Pyramid for LLM Applications

```
                    ┌─────────────────┐
                    │  LLM-as-Judge   │  ← Expensive, high-signal
                    │     Tests       │     (run on CI/weekly)
                    ├─────────────────┤
                    │   Integration   │  ← Real API calls
                    │     Tests       │     (run on release)
                  ┌─┴─────────────────┴─┐
                  │   Golden Sample     │  ← Fuzzy matching
                  │       Tests         │     (run on PR)
                ┌─┴─────────────────────┴─┐
                │    Property-Based       │  ← Invariant checking
                │         Tests           │     (run on commit)
              ┌─┴─────────────────────────┴─┐
              │      Contract/Schema        │  ← Structure validation
              │           Tests             │     (run on commit)
            ┌─┴─────────────────────────────┴─┐
            │        Mock-Based Tests         │  ← Deterministic logic
            │                                 │     (run always)
          ┌─┴─────────────────────────────────┴─┐
          │           Unit Tests                │  ← No LLM calls
          │   (parsing, config, file reading)   │     (run always)
          └─────────────────────────────────────┘
```

## 1. Unit Tests (No LLM Calls)

These test deterministic functionality that doesn't involve LLM calls.

### What to Test
- **Configuration management** (`config.py`)
  - Loading/saving config
  - Validation of experience levels, focus areas
  - API key handling (locked vs unlocked)
  - Config precedence (env > user > system > defaults)

- **File reading** (`file_reader.py`)
  - Language detection
  - Encoding handling
  - Metadata extraction
  - Directory scanning

- **Response parsing** (`analyzer.py`, `teaching_session.py`, `exercise_generator.py`)
  - `_parse_initial_response()` - extracting questions and observations
  - `_parse_code_response()` - extracting code, student question, issues
  - `_parse_exercise_response()` - extracting all exercise components
  - `_parse_evaluation_response()` - extracting understanding status

- **Logging** (`logger.py`)
  - Session start/end
  - Event logging
  - Export functionality

### Example Test Cases

```python
# tests/test_parsing.py
def test_parse_initial_response_extracts_questions():
    """Test that questions are correctly extracted from LLM response."""
    response = """## Questions

1. Why did you choose to use a dictionary here instead of a class?
2. What happens when the input is empty?

## Initial Observations

- The code follows a clear functional style
- Error handling is comprehensive
"""
    analyzer = CodeAnalyzer(api_key="fake", model="fake")
    result = analyzer._parse_initial_response(response)

    assert len(result["questions"]) == 2
    assert "dictionary" in result["questions"][0]
    assert len(result["observations"]) == 2


def test_parse_initial_response_handles_malformed():
    """Test graceful handling of malformed responses."""
    response = "Just some text without proper sections"
    analyzer = CodeAnalyzer(api_key="fake", model="fake")
    result = analyzer._parse_initial_response(response)

    assert result["questions"] == []
    assert result["observations"] == []
    assert result["raw_response"] == response
```

## 2. Mock-Based Tests

Test the logic flow without making real API calls.

### Strategy
- Mock `anthropic.Anthropic.messages.create()`
- Return predefined responses
- Verify correct prompts are constructed
- Test conversation history management

### Example Test Cases

```python
# tests/test_analyzer_mocked.py
from unittest.mock import Mock, patch

def test_analyze_code_builds_correct_prompt():
    """Verify prompt includes all necessary context."""
    with patch('anthropic.Anthropic') as mock_client:
        mock_response = Mock()
        mock_response.content = [Mock(text="## Questions\n1. Test?\n\n## Initial Observations\n- Test")]
        mock_client.return_value.messages.create.return_value = mock_response

        analyzer = CodeAnalyzer(api_key="test", model="claude-sonnet-4-5")
        result = analyzer.analyze_code(
            code="def hello(): pass",
            file_metadata={"language": "Python", "line_count": 1, "name": "test.py"},
            experience_level="intermediate",
            preferences={"focus_areas": ["design"], "question_style": "socratic"}
        )

        # Verify the call was made
        call_args = mock_client.return_value.messages.create.call_args
        prompt = call_args.kwargs["messages"][0]["content"]

        # Check prompt contains expected elements
        assert "intermediate" in prompt
        assert "Python" in prompt
        assert "def hello(): pass" in prompt
        assert "socratic" in prompt


def test_conversation_history_maintained():
    """Verify conversation history accumulates correctly."""
    with patch('anthropic.Anthropic') as mock_client:
        mock_response = Mock()
        mock_response.content = [Mock(text="## Questions\n1. Test?\n\n## Initial Observations\n- Test")]
        mock_client.return_value.messages.create.return_value = mock_response

        analyzer = CodeAnalyzer(api_key="test", model="claude-sonnet-4-5")

        # First call
        analyzer.analyze_code(
            code="test code",
            file_metadata={"language": "Python"},
            experience_level="beginner",
            preferences={}
        )

        assert len(analyzer.conversation_history) == 2  # user + assistant

        # Second call (process_answers)
        mock_response.content = [Mock(text="Feedback response")]
        analyzer.process_answers(["Answer 1"], "beginner", {})

        assert len(analyzer.conversation_history) == 4  # 2 + 2 more
```

## 3. Contract/Schema Tests

Verify that LLM outputs conform to expected structure.

### Strategy
- Test against real or captured LLM responses
- Validate structure, not content
- Use relaxed validators that allow variations

### Expected Contracts

```python
# tests/contracts.py
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class InitialAnalysisContract:
    """Contract for initial code analysis response."""
    min_questions: int = 1
    max_questions: int = 5
    min_observations: int = 1
    max_observations: int = 10

    def validate(self, result: dict) -> List[str]:
        errors = []
        questions = result.get("questions", [])
        observations = result.get("observations", [])

        if len(questions) < self.min_questions:
            errors.append(f"Too few questions: {len(questions)} < {self.min_questions}")
        if len(questions) > self.max_questions:
            errors.append(f"Too many questions: {len(questions)} > {self.max_questions}")
        if len(observations) < self.min_observations:
            errors.append(f"Too few observations: {len(observations)} < {self.min_observations}")

        return errors


@dataclass
class ExerciseContract:
    """Contract for generated exercises."""
    required_sections = ["instructions", "starter_code", "hints"]
    min_hints: int = 2
    min_instruction_length: int = 100  # characters

    def validate(self, result: dict) -> List[str]:
        errors = []

        for section in self.required_sections:
            if not result.get(section):
                errors.append(f"Missing required section: {section}")

        hints = result.get("hints", [])
        if len(hints) < self.min_hints:
            errors.append(f"Too few hints: {len(hints)} < {self.min_hints}")

        instructions = result.get("instructions", "")
        if len(instructions) < self.min_instruction_length:
            errors.append(f"Instructions too short: {len(instructions)} chars")

        return errors
```

### Example Tests

```python
# tests/test_contracts.py
import pytest
from tests.contracts import InitialAnalysisContract, ExerciseContract

# These would use captured/recorded responses
SAMPLE_ANALYSIS_RESPONSES = [
    # Response 1: Well-formatted
    """## Questions

1. Why did you choose recursion here?
2. What's the expected input size?

## Initial Observations

- Clean structure
- Good naming conventions
""",
    # Response 2: Slightly different format
    """## Question

1. What trade-offs did you consider for this approach?
2. How do you handle the edge case of empty input?
3. Is there a reason you didn't use the standard library here?

## Observations

- The code is well-organized
- Error handling could be more comprehensive
"""
]


@pytest.mark.parametrize("response", SAMPLE_ANALYSIS_RESPONSES)
def test_analysis_response_meets_contract(response):
    """Test that analysis responses meet the structural contract."""
    from code_tutor.analyzer import CodeAnalyzer

    analyzer = CodeAnalyzer(api_key="fake", model="fake")
    result = analyzer._parse_initial_response(response)

    contract = InitialAnalysisContract()
    errors = contract.validate(result)

    assert not errors, f"Contract violations: {errors}"
```

## 4. Property-Based Tests

Test invariants that should always hold regardless of specific content.

### Properties to Test

| Property | Description |
|----------|-------------|
| **Experience-appropriate language** | Beginner responses shouldn't use unexplained jargon |
| **Question count bounds** | Always 1-5 questions |
| **Response references input** | Feedback should relate to the submitted code |
| **Consistent tone** | Should be educational, not critical |
| **Format stability** | Parseable structure maintained |

### Example Tests

```python
# tests/test_properties.py
import pytest
from hypothesis import given, strategies as st

# Common jargon that shouldn't appear unexplained for beginners
ADVANCED_JARGON = [
    "monad", "functor", "polymorphism", "covariance", "contravariance",
    "memoization", "currying", "thunk", "continuation"
]


def test_beginner_responses_avoid_unexplained_jargon(captured_beginner_responses):
    """Verify beginner-level responses don't use unexplained advanced terms."""
    for response in captured_beginner_responses:
        for term in ADVANCED_JARGON:
            if term.lower() in response.lower():
                # Term appears - verify it's explained
                # Check for patterns like "X (which means...)" or "X: ..."
                context_window = 200  # characters around the term
                idx = response.lower().find(term.lower())
                context = response[max(0, idx-50):idx+context_window]

                explanation_patterns = [
                    f"{term} (", f"{term}, which", f"{term} means",
                    f"{term} is", f"called {term}"
                ]
                has_explanation = any(p.lower() in context.lower() for p in explanation_patterns)

                assert has_explanation, f"Advanced term '{term}' used without explanation for beginner"


def test_feedback_references_submitted_code(analyzer, sample_codes):
    """Verify feedback is specific to the submitted code, not generic."""
    for code, metadata in sample_codes:
        result = analyzer.analyze_code(code, metadata, "intermediate", {})

        # Feedback should mention specific elements from the code
        code_identifiers = extract_identifiers(code)  # function names, variables

        response = result.get("raw_response", "")

        # At least some identifiers should appear in the response
        matches = sum(1 for ident in code_identifiers if ident in response)

        assert matches > 0, "Response appears generic, doesn't reference specific code elements"


def test_question_count_bounded():
    """Questions should always be between 1 and 5."""
    # This would run against multiple captured responses
    for response in captured_responses:
        result = parse_initial_response(response)
        questions = result.get("questions", [])

        assert 1 <= len(questions) <= 5, f"Question count {len(questions)} out of bounds"
```

## 5. Golden Sample Tests (Fuzzy Matching)

Compare against known-good examples using semantic similarity rather than exact matching.

### Strategy
- Maintain a corpus of "golden" input/output pairs
- Use embedding-based similarity or keyword matching
- Set thresholds for acceptable similarity
- Alert on significant deviations

### Golden Sample Structure

```
tests/
  golden_samples/
    code_review/
      sample_001/
        input.json        # Code, metadata, preferences
        expected.json     # Expected structure and key phrases
      sample_002/
        ...
    teaching/
      sample_001/
        ...
    exercises/
      sample_001/
        ...
```

### Example Implementation

```python
# tests/test_golden_samples.py
import json
from pathlib import Path
from difflib import SequenceMatcher

GOLDEN_SAMPLES_DIR = Path(__file__).parent / "golden_samples"


def load_golden_sample(category: str, sample_id: str) -> tuple:
    """Load a golden sample input/expected pair."""
    sample_dir = GOLDEN_SAMPLES_DIR / category / sample_id

    with open(sample_dir / "input.json") as f:
        input_data = json.load(f)
    with open(sample_dir / "expected.json") as f:
        expected = json.load(f)

    return input_data, expected


def semantic_similarity(text1: str, text2: str) -> float:
    """Calculate semantic similarity between two texts."""
    # Simple implementation using SequenceMatcher
    # Could be enhanced with embeddings
    return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()


def keyword_coverage(response: str, keywords: list) -> float:
    """Calculate what percentage of expected keywords appear."""
    if not keywords:
        return 1.0
    matches = sum(1 for kw in keywords if kw.lower() in response.lower())
    return matches / len(keywords)


class GoldenSampleTest:
    """Test against golden samples with fuzzy matching."""

    def __init__(self, similarity_threshold: float = 0.3, keyword_threshold: float = 0.6):
        self.similarity_threshold = similarity_threshold
        self.keyword_threshold = keyword_threshold

    def validate(self, actual_response: str, expected: dict) -> dict:
        """
        Validate a response against expected golden sample.

        Args:
            actual_response: The actual LLM response
            expected: Dict with 'keywords', 'expected_sections', 'anti_patterns'

        Returns:
            Dict with pass/fail status and details
        """
        results = {"passed": True, "issues": []}

        # Check keyword coverage
        keywords = expected.get("keywords", [])
        if keywords:
            coverage = keyword_coverage(actual_response, keywords)
            if coverage < self.keyword_threshold:
                results["passed"] = False
                results["issues"].append(
                    f"Keyword coverage {coverage:.2%} below threshold {self.keyword_threshold:.2%}"
                )

        # Check for required sections
        for section in expected.get("expected_sections", []):
            if section.lower() not in actual_response.lower():
                results["passed"] = False
                results["issues"].append(f"Missing expected section: {section}")

        # Check for anti-patterns (things that should NOT appear)
        for anti in expected.get("anti_patterns", []):
            if anti.lower() in actual_response.lower():
                results["passed"] = False
                results["issues"].append(f"Found anti-pattern: {anti}")

        return results


# Example golden sample expected.json:
# {
#   "keywords": ["recursion", "base case", "stack", "performance"],
#   "expected_sections": ["## Questions", "## Initial Observations"],
#   "anti_patterns": ["terrible", "wrong", "bad code"],
#   "notes": "Should ask about base case and termination condition"
# }
```

## 6. LLM-as-Judge Tests

Use an LLM to evaluate the quality of another LLM's outputs.

### Strategy
- Use a smaller/cheaper model as evaluator
- Define clear rubrics for evaluation
- Run periodically (expensive but high-signal)
- Track scores over time for regression detection

### Evaluation Dimensions

| Dimension | Description | Weight |
|-----------|-------------|--------|
| **Relevance** | Does response address the code/question? | 25% |
| **Helpfulness** | Would this help the learner improve? | 25% |
| **Tone** | Is it encouraging and educational? | 20% |
| **Accuracy** | Are technical suggestions correct? | 20% |
| **Clarity** | Is the response clear and well-organized? | 10% |

### Implementation

```python
# tests/test_llm_judge.py
import anthropic
from dataclasses import dataclass
from typing import Optional
import json


@dataclass
class EvaluationResult:
    relevance: int  # 1-5
    helpfulness: int  # 1-5
    tone: int  # 1-5
    accuracy: int  # 1-5
    clarity: int  # 1-5
    overall: float
    reasoning: str

    @property
    def weighted_score(self) -> float:
        return (
            self.relevance * 0.25 +
            self.helpfulness * 0.25 +
            self.tone * 0.20 +
            self.accuracy * 0.20 +
            self.clarity * 0.10
        )


class LLMJudge:
    """Uses an LLM to evaluate response quality."""

    EVALUATION_PROMPT = """You are evaluating an AI code tutor's response. Rate each dimension 1-5.

## Context
- Learner experience level: {experience_level}
- Code being reviewed:
```
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

Respond in JSON format:
{{
  "relevance": <1-5>,
  "helpfulness": <1-5>,
  "tone": <1-5>,
  "accuracy": <1-5>,
  "clarity": <1-5>,
  "reasoning": "<brief explanation of scores>"
}}"""

    def __init__(self, api_key: str, model: str = "claude-haiku-4-5"):
        """Use a fast/cheap model for evaluation."""
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def evaluate(
        self,
        code: str,
        response: str,
        experience_level: str
    ) -> EvaluationResult:
        """Evaluate a code review response."""
        prompt = self.EVALUATION_PROMPT.format(
            experience_level=experience_level,
            code=code,
            response=response
        )

        result = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse JSON response
        content = result.content[0].text
        # Handle potential markdown code blocks
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        data = json.loads(content.strip())

        eval_result = EvaluationResult(
            relevance=data["relevance"],
            helpfulness=data["helpfulness"],
            tone=data["tone"],
            accuracy=data["accuracy"],
            clarity=data["clarity"],
            overall=0,
            reasoning=data["reasoning"]
        )
        eval_result.overall = eval_result.weighted_score

        return eval_result


# Test usage
def test_code_review_quality(api_key):
    """Run LLM-as-judge evaluation on code review responses."""
    judge = LLMJudge(api_key)

    # Test case
    code = '''
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
'''

    # Simulated tutor response
    tutor_response = """## Questions

1. Have you considered what happens with large values of n?
2. What was your reasoning for using recursion here?

## Initial Observations

- The base case handling is correct
- The recursive structure follows the mathematical definition
- This implementation has exponential time complexity
"""

    result = judge.evaluate(code, tutor_response, "intermediate")

    # Set minimum quality thresholds
    assert result.relevance >= 3, f"Relevance too low: {result.relevance}"
    assert result.helpfulness >= 3, f"Helpfulness too low: {result.helpfulness}"
    assert result.tone >= 4, f"Tone too low: {result.tone}"
    assert result.overall >= 3.5, f"Overall score too low: {result.overall}"
```

## 7. Integration Tests

Full end-to-end tests with real API calls.

### Strategy
- Run sparingly (expensive)
- Test complete user flows
- Capture responses for golden sample corpus
- Run before releases

### Example Tests

```python
# tests/test_integration.py
import pytest
import os

# Skip if no API key available
pytestmark = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set"
)


@pytest.fixture
def api_key():
    return os.environ["ANTHROPIC_API_KEY"]


class TestCodeReviewIntegration:
    """Integration tests for code review flow."""

    def test_complete_review_flow(self, api_key):
        """Test complete code review from analysis to feedback."""
        from code_tutor.analyzer import CodeAnalyzer
        from tests.contracts import InitialAnalysisContract

        analyzer = CodeAnalyzer(api_key=api_key, model="claude-haiku-4-5")

        code = '''
def quicksort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + middle + quicksort(right)
'''

        # Step 1: Initial analysis
        result = analyzer.analyze_code(
            code=code,
            file_metadata={"language": "Python", "line_count": 9, "name": "sort.py"},
            experience_level="intermediate",
            preferences={"focus_areas": ["performance"], "question_style": "socratic"}
        )

        # Validate structure
        contract = InitialAnalysisContract()
        errors = contract.validate(result)
        assert not errors, f"Contract violations: {errors}"

        # Step 2: Process answers
        answers = [
            "I chose the middle element as pivot for simplicity",
            "This is for sorting small to medium arrays, not performance critical"
        ]

        feedback = analyzer.process_answers(
            answers=answers,
            experience_level="intermediate",
            preferences={"focus_areas": ["performance"]}
        )

        # Basic validation
        assert "feedback" in feedback
        assert len(feedback["feedback"]) > 100  # Substantive response

        # Step 3: Follow-up
        followup = analyzer.continue_conversation(
            "Can you explain more about the space complexity?"
        )

        assert len(followup) > 50
        assert "space" in followup.lower() or "memory" in followup.lower()


class TestExerciseGenerationIntegration:
    """Integration tests for exercise generation."""

    def test_generate_and_review_exercise(self, api_key):
        """Test generating an exercise and reviewing a submission."""
        from code_tutor.exercise_generator import ExerciseGenerator
        from tests.contracts import ExerciseContract

        generator = ExerciseGenerator(api_key=api_key, model="claude-haiku-4-5")

        # Generate exercise
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

        # Simulate submission review
        submission = '''
def binary_search(arr, target):
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
            original_exercise={"topic": "binary search", "exercise_type": "implementation"},
            submitted_code=submission,
            language="Python",
            experience_level="intermediate"
        )

        assert "feedback" in review
        assert review["assessment"] in ["NEEDS_WORK", "ACCEPTABLE", "GOOD", "EXCELLENT"]
```

## 8. Metrics and Evaluation Framework

Track quality over time to detect regressions.

### Metrics to Track

| Metric | How to Measure | Alert Threshold |
|--------|---------------|-----------------|
| Parse success rate | % responses that parse correctly | < 95% |
| Question count avg | Mean questions per analysis | Outside 2-4 |
| Keyword coverage | % expected keywords present | < 60% |
| LLM-judge scores | Weighted evaluation scores | < 3.5/5 |
| Response latency | Time to generate response | > 30s |
| Token usage | Input/output tokens | > 2x baseline |

### Implementation

```python
# tests/metrics.py
import json
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Optional


@dataclass
class TestRunMetrics:
    """Metrics from a single test run."""
    timestamp: str
    git_sha: str
    model: str

    # Parsing metrics
    parse_success_rate: float
    avg_questions: float
    avg_observations: float

    # Quality metrics (from LLM-judge)
    avg_relevance: Optional[float] = None
    avg_helpfulness: Optional[float] = None
    avg_tone: Optional[float] = None
    avg_overall: Optional[float] = None

    # Performance metrics
    avg_latency_ms: float = 0
    avg_input_tokens: int = 0
    avg_output_tokens: int = 0


class MetricsTracker:
    """Track and store test metrics over time."""

    def __init__(self, metrics_file: Path):
        self.metrics_file = metrics_file
        self.current_run: List[dict] = []

    def record(self, metric_name: str, value: float, tags: dict = None):
        """Record a single metric."""
        self.current_run.append({
            "metric": metric_name,
            "value": value,
            "tags": tags or {},
            "timestamp": datetime.now().isoformat()
        })

    def save_run(self, run_metrics: TestRunMetrics):
        """Save completed run metrics."""
        history = self._load_history()
        history.append(asdict(run_metrics))

        with open(self.metrics_file, 'w') as f:
            json.dump(history, f, indent=2)

    def _load_history(self) -> List[dict]:
        """Load historical metrics."""
        if self.metrics_file.exists():
            with open(self.metrics_file) as f:
                return json.load(f)
        return []

    def check_regression(self, current: TestRunMetrics, threshold_pct: float = 10) -> List[str]:
        """
        Check for regressions against historical baseline.

        Returns list of regression warnings.
        """
        history = self._load_history()
        if len(history) < 3:
            return []  # Not enough history

        # Calculate baseline from last 5 runs
        recent = history[-5:]
        warnings = []

        metrics_to_check = [
            ("parse_success_rate", "higher_better"),
            ("avg_overall", "higher_better"),
            ("avg_latency_ms", "lower_better"),
        ]

        for metric_name, direction in metrics_to_check:
            baseline_values = [r.get(metric_name) for r in recent if r.get(metric_name)]
            if not baseline_values:
                continue

            baseline = sum(baseline_values) / len(baseline_values)
            current_val = getattr(current, metric_name, None)

            if current_val is None:
                continue

            if direction == "higher_better":
                if current_val < baseline * (1 - threshold_pct / 100):
                    warnings.append(
                        f"{metric_name} regressed: {current_val:.2f} vs baseline {baseline:.2f}"
                    )
            else:  # lower_better
                if current_val > baseline * (1 + threshold_pct / 100):
                    warnings.append(
                        f"{metric_name} regressed: {current_val:.2f} vs baseline {baseline:.2f}"
                    )

        return warnings
```

## 9. CI/CD Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/llm-tests.yml
name: LLM Regression Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 6 * * 1'  # Weekly on Monday

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -e ".[dev]"
      - run: pytest tests/test_parsing.py tests/test_config.py -v

  contract-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -e ".[dev]"
      - run: pytest tests/test_contracts.py -v

  golden-sample-tests:
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request'
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -e ".[dev]"
      - run: pytest tests/test_golden_samples.py -v

  integration-tests:
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    env:
      ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -e ".[dev]"
      - run: pytest tests/test_integration.py -v --tb=short

  llm-judge-tests:
    runs-on: ubuntu-latest
    if: github.event_name == 'schedule'
    env:
      ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -e ".[dev]"
      - run: pytest tests/test_llm_judge.py -v
      - name: Upload metrics
        uses: actions/upload-artifact@v4
        with:
          name: test-metrics
          path: tests/metrics/
```

## 10. Test Data Management

### Recording Responses

```python
# tests/conftest.py
import pytest
import json
from pathlib import Path
from datetime import datetime


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
```

## Summary

This testing strategy provides multiple layers of confidence:

1. **Fast feedback** from unit and mock tests (run on every commit)
2. **Structural validation** from contract tests (run on every commit)
3. **Behavioral validation** from property and golden sample tests (run on PRs)
4. **Quality validation** from LLM-judge tests (run weekly)
5. **Regression detection** from metrics tracking (continuous)

The key insight is that for LLM applications, we test **properties and contracts**, not **exact outputs**. This allows the LLM to have natural variation while still ensuring consistent quality.

## Getting Started

1. Create the test directory structure
2. Add pytest to your dev dependencies (already in pyproject.toml)
3. Start with unit tests for parsing functions
4. Add contract tests for expected output structure
5. Build golden sample corpus over time
6. Add LLM-judge tests for periodic quality checks
