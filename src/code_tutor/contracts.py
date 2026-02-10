"""Shared prompt contracts and JSON parsers for LLM workflows."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, Optional, TypeVar

from .models import (
    CodeInitialAnalysisResult,
    ExerciseGenerationResult,
    ExerciseReviewResult,
    ProofInitialAnalysisResult,
)
from .response_parsing import (
    extract_json_object,
    parse_bool_value,
    parse_string_list,
    parse_string_value,
)

ParsedT = TypeVar("ParsedT")


class LLMWorkflowContract(ABC, Generic[ParsedT]):
    """Base contract for LLM prompt output shape + JSON parsing."""

    @property
    @abstractmethod
    def schema(self) -> str:
        """JSON schema snippet used in prompt instructions."""

    @property
    def extra_requirements(self) -> str:
        """Additional workflow-specific output requirements."""
        return ""

    def format_instructions(self) -> str:
        """Standardized prompt format instructions for this contract."""
        lines = [
            "Return ONLY valid JSON (no markdown, no prose) with this schema:",
            self.schema,
        ]
        extra = self.extra_requirements.strip()
        if extra:
            lines.extend(["", extra])
        return "\n".join(lines)

    def parse_response(self, response: str) -> Optional[ParsedT]:
        """Parse a model response into a typed output, if JSON is present."""
        payload = extract_json_object(response)
        if payload is None:
            return None
        return self.parse_payload(payload, response)

    @abstractmethod
    def parse_payload(self, payload: Dict[str, Any], raw_response: str) -> Optional[ParsedT]:
        """Parse JSON payload into a typed output."""


class CodeInitialAnalysisContract(LLMWorkflowContract[CodeInitialAnalysisResult]):
    """Contract for initial code analysis."""

    @property
    def schema(self) -> str:
        return (
            "{\n"
            '  "questions": ["question 1", "question 2", "question 3"],\n'
            '  "observations": ["observation 1", "observation 2", "observation 3"]\n'
            "}"
        )

    @property
    def extra_requirements(self) -> str:
        return "\n".join(
            [
                "Requirements:",
                "- Ask 2-4 questions.",
                "- Keep observations brief and neutral.",
            ]
        )

    def parse_payload(
        self,
        payload: Dict[str, Any],
        raw_response: str,
    ) -> Optional[CodeInitialAnalysisResult]:
        questions = parse_string_list(payload, "questions")
        observations = parse_string_list(payload, "observations")
        if not questions and not observations:
            return None
        return CodeInitialAnalysisResult(
            questions=questions,
            observations=observations,
            raw_response=raw_response,
        )


class ProofInitialAnalysisContract(LLMWorkflowContract[ProofInitialAnalysisResult]):
    """Contract for initial proof analysis."""

    @property
    def schema(self) -> str:
        return (
            "{\n"
            '  "main_claim": "One sentence describing what is being proved",\n'
            '  "questions": ["question 1", "question 2", "question 3"],\n'
            '  "observations": ["observation 1", "observation 2", "observation 3"]\n'
            "}"
        )

    @property
    def extra_requirements(self) -> str:
        return "\n".join(
            [
                "Requirements:",
                "- Ask 2-4 questions.",
                "- Keep observations brief and neutral.",
            ]
        )

    def parse_payload(
        self,
        payload: Dict[str, Any],
        raw_response: str,
    ) -> Optional[ProofInitialAnalysisResult]:
        main_claim = parse_string_value(payload, "main_claim", "")
        questions = parse_string_list(payload, "questions")
        observations = parse_string_list(payload, "observations")
        if not main_claim and not questions and not observations:
            return None
        return ProofInitialAnalysisResult(
            main_claim=main_claim,
            questions=questions,
            observations=observations,
            raw_response=raw_response,
        )


class ExerciseGenerationContract(LLMWorkflowContract[ExerciseGenerationResult]):
    """Contract for generated exercise content."""

    @property
    def schema(self) -> str:
        return (
            "{\n"
            '  "instructions": "Detailed learner instructions (2-4 paragraphs)",\n'
            '  "learning_objectives": ["objective 1", "objective 2", "objective 3"],\n'
            '  "starter_code": "Code template/buggy code/signature",\n'
            '  "test_code": "Optional runnable tests, or empty string",\n'
            '  "hints": ["hint 1", "hint 2", "hint 3"],\n'
            '  "solution_explanation": "Brief hidden solution explanation"\n'
            "}"
        )

    def parse_payload(
        self,
        payload: Dict[str, Any],
        raw_response: str,
    ) -> Optional[ExerciseGenerationResult]:
        instructions = parse_string_value(payload, "instructions", "")
        learning_objectives = parse_string_list(payload, "learning_objectives")
        starter_code = parse_string_value(payload, "starter_code", "")
        test_code = parse_string_value(payload, "test_code", "")
        hints = parse_string_list(payload, "hints")
        solution_explanation = parse_string_value(payload, "solution_explanation", "")

        if not instructions and not starter_code and not learning_objectives and not hints:
            return None

        return ExerciseGenerationResult(
            instructions=instructions,
            learning_objectives=learning_objectives,
            starter_code=starter_code,
            test_code=test_code,
            hints=hints,
            solution_explanation=solution_explanation,
        )


class ExerciseReviewContract(LLMWorkflowContract[ExerciseReviewResult]):
    """Contract for exercise submission reviews."""

    ASSESSMENTS = ("NEEDS_WORK", "ACCEPTABLE", "GOOD", "EXCELLENT")

    @property
    def schema(self) -> str:
        return (
            "{\n"
            '  "feedback_markdown": "Markdown feedback with sections: Correctness, '
            'Code Quality, Understanding Demonstrated, Suggestions, Overall Assessment",\n'
            '  "assessment": "NEEDS_WORK | ACCEPTABLE | GOOD | EXCELLENT"\n'
            "}"
        )

    def parse_payload(
        self,
        payload: Dict[str, Any],
        raw_response: str,
    ) -> Optional[ExerciseReviewResult]:
        feedback = parse_string_value(payload, "feedback_markdown", "")
        if not feedback:
            feedback = parse_string_value(payload, "feedback", "")
        if not feedback:
            return None

        assessment = parse_string_value(payload, "assessment", "ACCEPTABLE")
        return ExerciseReviewResult(
            feedback=feedback,
            assessment=self.normalize_assessment(assessment),
        )

    @classmethod
    def normalize_assessment(cls, value: str) -> str:
        """Normalize review assessment to a known constant."""
        normalized = (value or "").strip().upper()
        if normalized in cls.ASSESSMENTS:
            return normalized
        for label in cls.ASSESSMENTS[::-1]:
            if label in normalized:
                return label
        return "ACCEPTABLE"


class TeachingCodeExampleContract(LLMWorkflowContract[Dict[str, Any]]):
    """Contract for teach-me flawed code examples."""

    @property
    def schema(self) -> str:
        return (
            "{\n"
            '  "code": "Flawed code snippet",\n'
            '  "student_question": "Authentic question from the student perspective",\n'
            '  "issues": ["Issue 1", "Issue 2"]\n'
            "}"
        )

    @property
    def extra_requirements(self) -> str:
        return "\n".join(
            [
                "Requirements:",
                "- `code` should be 5-15 lines.",
                "- `issues` should include the key hidden mistakes.",
            ]
        )

    def parse_payload(
        self,
        payload: Dict[str, Any],
        raw_response: str,
    ) -> Optional[Dict[str, Any]]:
        code = parse_string_value(payload, "code", "")
        student_question = parse_string_value(payload, "student_question", "")
        issues = parse_string_list(payload, "issues")
        if not code and not student_question and not issues:
            return None
        return {
            "code": code,
            "student_question": student_question,
            "issues": issues,
        }


class TeachingEvaluationContract(LLMWorkflowContract[Dict[str, Any]]):
    """Contract for teach-me evaluation output."""

    @property
    def schema(self) -> str:
        return (
            "{\n"
            '  "student_response_markdown": "Student response in character",\n'
            '  "teaching_quality_assessment": "Brief internal note on teaching quality",\n'
            '  "understanding_achieved": true\n'
            "}"
        )

    def parse_payload(
        self,
        payload: Dict[str, Any],
        raw_response: str,
    ) -> Optional[Dict[str, Any]]:
        understanding = parse_bool_value(payload, "understanding_achieved")
        student_response = parse_string_value(payload, "student_response_markdown", "")
        quality = parse_string_value(payload, "teaching_quality_assessment", "")

        if understanding is None or (not student_response and not quality):
            return None

        feedback_parts = []
        if student_response:
            feedback_parts.append(student_response)
        if quality:
            feedback_parts.append(f"## Teaching Quality Assessment\n{quality}")

        return {
            "understanding_achieved": understanding,
            "feedback": "\n\n".join(feedback_parts),
        }


class ProofTeachingExampleContract(LLMWorkflowContract[Dict[str, Any]]):
    """Contract for generated flawed proofs in teaching mode."""

    @property
    def schema(self) -> str:
        return (
            "{\n"
            '  "theorem": "The theorem or claim being proved",\n'
            '  "flawed_proof": "The proof body with intentional issues",\n'
            '  "issues": ["Issue 1", "Issue 2"]\n'
            "}"
        )

    def parse_payload(
        self,
        payload: Dict[str, Any],
        raw_response: str,
    ) -> Optional[Dict[str, Any]]:
        theorem = parse_string_value(payload, "theorem", "")
        proof = parse_string_value(payload, "flawed_proof", "")
        if not proof:
            proof = parse_string_value(payload, "proof", "")
        issues = parse_string_list(payload, "issues")

        if not theorem and not proof and not issues:
            return None

        return {
            "theorem": theorem,
            "proof": proof,
            "issues": issues,
        }


class ProofTeachingEvaluationContract(LLMWorkflowContract[Dict[str, Any]]):
    """Contract for proof teaching evaluation output."""

    @property
    def schema(self) -> str:
        return (
            "{\n"
            '  "feedback_markdown": "Constructive feedback on the analysis",\n'
            '  "understanding_achieved": true\n'
            "}"
        )

    def parse_payload(
        self,
        payload: Dict[str, Any],
        raw_response: str,
    ) -> Optional[Dict[str, Any]]:
        understanding = parse_bool_value(payload, "understanding_achieved")
        feedback = parse_string_value(payload, "feedback_markdown", "")
        if not feedback:
            feedback = parse_string_value(payload, "feedback", "")

        if understanding is None or not feedback:
            return None

        return {
            "understanding_achieved": understanding,
            "feedback": feedback,
        }


CODE_INITIAL_ANALYSIS_CONTRACT = CodeInitialAnalysisContract()
PROOF_INITIAL_ANALYSIS_CONTRACT = ProofInitialAnalysisContract()
EXERCISE_GENERATION_CONTRACT = ExerciseGenerationContract()
EXERCISE_REVIEW_CONTRACT = ExerciseReviewContract()
TEACHING_CODE_EXAMPLE_CONTRACT = TeachingCodeExampleContract()
TEACHING_EVALUATION_CONTRACT = TeachingEvaluationContract()
PROOF_TEACHING_EXAMPLE_CONTRACT = ProofTeachingExampleContract()
PROOF_TEACHING_EVALUATION_CONTRACT = ProofTeachingEvaluationContract()
