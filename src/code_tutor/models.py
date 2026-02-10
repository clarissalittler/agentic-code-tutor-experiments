"""Core typed result models for analyzer and exercise workflows."""

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class CodeInitialAnalysisResult:
    """Structured result for an initial code analysis pass."""

    questions: List[str]
    observations: List[str]
    raw_response: str


@dataclass(frozen=True)
class CodeFeedbackResult:
    """Structured result for code feedback generation."""

    feedback: str
    raw_response: str


@dataclass(frozen=True)
class ProofInitialAnalysisResult:
    """Structured result for an initial proof analysis pass."""

    main_claim: str
    questions: List[str]
    observations: List[str]
    raw_response: str


@dataclass(frozen=True)
class ProofFeedbackResult:
    """Structured result for proof feedback generation."""

    feedback: str
    raw_response: str


@dataclass(frozen=True)
class ExerciseGenerationResult:
    """Structured result for generated exercise content."""

    instructions: str
    learning_objectives: List[str]
    starter_code: str
    test_code: str
    hints: List[str]
    solution_explanation: str


@dataclass(frozen=True)
class ExerciseReviewResult:
    """Structured result for review of a submitted exercise."""

    feedback: str
    assessment: str
