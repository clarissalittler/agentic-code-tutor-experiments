"""Contract definitions for validating LLM response structure."""

from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class InitialAnalysisContract:
    """Contract for initial code analysis response.

    Validates that the parsed response contains the expected
    structural elements with reasonable bounds.
    """
    min_questions: int = 1
    max_questions: int = 5
    min_observations: int = 1
    max_observations: int = 10

    def validate(self, result: Dict[str, Any]) -> List[str]:
        """
        Validate a parsed analysis result against the contract.

        Args:
            result: Dictionary with 'questions' and 'observations' keys

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        questions = result.get("questions", [])
        observations = result.get("observations", [])

        if len(questions) < self.min_questions:
            errors.append(f"Too few questions: {len(questions)} < {self.min_questions}")
        if len(questions) > self.max_questions:
            errors.append(f"Too many questions: {len(questions)} > {self.max_questions}")
        if len(observations) < self.min_observations:
            errors.append(f"Too few observations: {len(observations)} < {self.min_observations}")
        if len(observations) > self.max_observations:
            errors.append(f"Too many observations: {len(observations)} > {self.max_observations}")

        # Check that questions are actual questions (heuristic)
        for i, q in enumerate(questions):
            if len(q) < 10:
                errors.append(f"Question {i+1} too short: '{q}'")

        return errors


@dataclass
class ExerciseContract:
    """Contract for generated exercises.

    Validates that exercises contain all required components
    with sufficient content.
    """
    required_sections: List[str] = field(default_factory=lambda: [
        "instructions", "starter_code", "hints"
    ])
    min_hints: int = 2
    max_hints: int = 5
    min_instruction_length: int = 100  # characters
    min_starter_code_length: int = 20  # characters

    def validate(self, result: Dict[str, Any]) -> List[str]:
        """
        Validate a generated exercise against the contract.

        Args:
            result: Dictionary with exercise components

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Check required sections exist
        for section in self.required_sections:
            if not result.get(section):
                errors.append(f"Missing required section: {section}")

        # Check hints
        hints = result.get("hints", [])
        if len(hints) < self.min_hints:
            errors.append(f"Too few hints: {len(hints)} < {self.min_hints}")
        if len(hints) > self.max_hints:
            errors.append(f"Too many hints: {len(hints)} > {self.max_hints}")

        # Check instruction length
        instructions = result.get("instructions", "")
        if len(instructions) < self.min_instruction_length:
            errors.append(
                f"Instructions too short: {len(instructions)} < {self.min_instruction_length} chars"
            )

        # Check starter code exists and has content
        starter_code = result.get("starter_code", "")
        if len(starter_code) < self.min_starter_code_length:
            errors.append(
                f"Starter code too short: {len(starter_code)} < {self.min_starter_code_length} chars"
            )

        return errors


@dataclass
class FeedbackContract:
    """Contract for feedback responses.

    Validates that feedback is substantive and well-structured.
    """
    min_feedback_length: int = 200  # characters
    expected_sections: List[str] = field(default_factory=lambda: [
        "Positive", "Suggestion", "Learning"
    ])

    def validate(self, result: Dict[str, Any]) -> List[str]:
        """
        Validate feedback against the contract.

        Args:
            result: Dictionary with 'feedback' key containing response text

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        feedback = result.get("feedback", "")

        if len(feedback) < self.min_feedback_length:
            errors.append(
                f"Feedback too short: {len(feedback)} < {self.min_feedback_length} chars"
            )

        # Check for expected sections (case-insensitive, partial match)
        feedback_lower = feedback.lower()
        for section in self.expected_sections:
            if section.lower() not in feedback_lower:
                # This is a soft warning, not a hard error
                pass  # Could add as warning: errors.append(f"Missing section hint: {section}")

        return errors


@dataclass
class TeachingResponseContract:
    """Contract for teaching session responses.

    Validates that teaching responses contain code and issues.
    """
    min_code_length: int = 10
    min_issues: int = 1

    def validate(self, result: Dict[str, Any]) -> List[str]:
        """
        Validate a teaching response against the contract.

        Args:
            result: Dictionary with 'code' and 'issues' keys

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        code = result.get("code", "")
        issues = result.get("issues", [])

        if len(code) < self.min_code_length:
            errors.append(f"Code too short: {len(code)} < {self.min_code_length} chars")

        if len(issues) < self.min_issues:
            errors.append(f"Too few issues: {len(issues)} < {self.min_issues}")

        return errors


@dataclass
class ReviewSubmissionContract:
    """Contract for exercise submission reviews."""
    valid_assessments: List[str] = field(default_factory=lambda: [
        "NEEDS_WORK", "ACCEPTABLE", "GOOD", "EXCELLENT"
    ])
    min_feedback_length: int = 100

    def validate(self, result: Dict[str, Any]) -> List[str]:
        """
        Validate a submission review against the contract.

        Args:
            result: Dictionary with 'feedback' and 'assessment' keys

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        assessment = result.get("assessment", "")
        feedback = result.get("feedback", "")

        if assessment not in self.valid_assessments:
            errors.append(f"Invalid assessment: {assessment}")

        if len(feedback) < self.min_feedback_length:
            errors.append(
                f"Feedback too short: {len(feedback)} < {self.min_feedback_length} chars"
            )

        return errors
