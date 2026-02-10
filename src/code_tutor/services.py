"""Service layer for mode orchestration outside CLI command handlers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from .cli_support import end_api_logger, start_api_logger
from .config import ConfigManager
from .exercise_generator import ExerciseGenerator
from .exercise_manager import ExerciseManager
from .models import ExerciseReviewResult
from .proof_reader import ProofReader


@dataclass(frozen=True)
class RoguelikeGenerationResult:
    """Result from generating an exercise run."""

    exercise_info: Dict[str, Any]
    model: str


@dataclass(frozen=True)
class RoguelikeSubmissionResult:
    """Result from reviewing a submitted exercise run."""

    exercise: Dict[str, Any]
    review: ExerciseReviewResult
    model: str


class ReviewModeService:
    """Orchestration service for code review mode."""

    def __init__(self, config_manager: ConfigManager, console: Any):
        self.config_manager = config_manager
        self.console = console

    def review_path(self, path: str, recursive: bool = True) -> None:
        """Run review mode for a file or directory path."""
        from .session import ReviewSession

        session = ReviewSession(self.config_manager, self.console)
        path_obj = Path(path)
        if path_obj.is_file():
            session.start_review(path)
            return
        if path_obj.is_dir():
            session.review_directory(path, recursive=recursive)
            return
        raise ValueError(f"Invalid path: {path}")


class TeachingModeService:
    """Orchestration service for teach-me mode."""

    def __init__(self, config_manager: ConfigManager, console: Any):
        self.config_manager = config_manager
        self.console = console

    def start(self) -> None:
        """Start an interactive teaching session."""
        from .teaching_session import TeachingSession

        session = TeachingSession(self.config_manager, self.console)
        session.start_session()


class ProofModeService:
    """Orchestration service for proof review and teaching modes."""

    def __init__(self, config_manager: ConfigManager, console: Any):
        self.config_manager = config_manager
        self.console = console

    @staticmethod
    def is_supported_file(file_path: str) -> bool:
        """Return whether a proof file is supported."""
        return ProofReader().is_supported(file_path)

    @staticmethod
    def supported_formats() -> Dict[str, str]:
        """Return supported proof format mapping."""
        return ProofReader.SUPPORTED_EXTENSIONS

    def review_file(
        self,
        file_path: str,
        domain: Optional[str] = None,
        experience_level: Optional[str] = None,
    ) -> None:
        """Run a proof review session for a file."""
        from .proof_session import ProofSession

        session = ProofSession(self.config_manager, self.console)
        session.start_review(file_path, domain=domain, experience_level=experience_level)

    def start_teaching(self, domain: Optional[str] = None) -> None:
        """Start proof teaching mode."""
        from .proof_session import ProofTeachingSession

        session = ProofTeachingSession(self.config_manager, self.console)
        session.start_session(domain=domain)


class RoguelikeModeService:
    """Orchestration service for roguelike exercise flows."""

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.manager = ExerciseManager(config_manager=config_manager)

    def generate_run(
        self,
        topic: str,
        language: str,
        exercise_type: str,
        difficulty: Optional[str] = None,
    ) -> RoguelikeGenerationResult:
        """Generate a new exercise run and persist it."""
        runtime = self.config_manager.get_llm_runtime()
        api_key = runtime.api_key
        model = runtime.model
        provider = runtime.provider
        base_url = runtime.base_url
        experience_level = self.config_manager.get("experience_level", "intermediate")
        resolved_difficulty = difficulty or experience_level

        api_logger = start_api_logger(
            self.config_manager,
            "exercise_generate",
            {
                "topic": topic,
                "language": language,
                "exercise_type": exercise_type,
                "difficulty": resolved_difficulty,
                "model": model,
            },
        )
        log_api_calls = api_logger is not None

        generator = ExerciseGenerator(
            api_key,
            model,
            provider=provider,
            base_url=base_url,
            logger=api_logger,
            log_api_calls=log_api_calls,
        )
        try:
            exercise_content = generator.generate_exercise(
                topic=topic,
                language=language,
                exercise_type=exercise_type,
                difficulty=resolved_difficulty,
                experience_level=experience_level,
            )
        finally:
            end_api_logger(api_logger)

        exercise_info = self.manager.create_exercise(
            topic=topic,
            language=language,
            exercise_type=exercise_type,
            difficulty=resolved_difficulty,
            instructions=exercise_content.instructions,
            starter_code=exercise_content.starter_code,
            solution_hints=exercise_content.hints,
            learning_objectives=exercise_content.learning_objectives,
            test_code=exercise_content.test_code or None,
        )
        return RoguelikeGenerationResult(
            exercise_info=exercise_info,
            model=model,
        )

    def list_runs(self, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """List stored exercise runs."""
        return self.manager.list_exercises(status_filter=status_filter)

    def get_run(self, exercise_path: str) -> Optional[Dict[str, Any]]:
        """Get a run by path or id."""
        return self.manager.get_exercise(exercise_path)

    def review_run_submission(self, exercise_path: str) -> RoguelikeSubmissionResult:
        """Grade a run submission and mark as reviewed."""
        exercise = self.manager.get_exercise(exercise_path)
        if not exercise:
            raise ValueError(f"Exercise not found: {exercise_path}")

        starter_file = exercise.get("starter_file")
        if not starter_file:
            raise ValueError("Could not find starter file in exercise.")

        with open(starter_file, "r", encoding="utf-8") as submitted_file:
            submitted_code = submitted_file.read()

        runtime = self.config_manager.get_llm_runtime()
        api_key = runtime.api_key
        model = runtime.model
        provider = runtime.provider
        base_url = runtime.base_url
        experience_level = self.config_manager.get("experience_level", "intermediate")

        self.manager.update_status(exercise_path, ExerciseManager.STATUS_SUBMITTED)

        api_logger = start_api_logger(
            self.config_manager,
            "exercise_submit",
            {
                "exercise_id": exercise.get("id"),
                "topic": exercise["metadata"].get("topic"),
                "exercise_type": exercise["metadata"].get("exercise_type"),
                "model": model,
            },
        )
        log_api_calls = api_logger is not None

        generator = ExerciseGenerator(
            api_key,
            model,
            provider=provider,
            base_url=base_url,
            logger=api_logger,
            log_api_calls=log_api_calls,
        )
        try:
            review = generator.review_submission(
                original_exercise=exercise["metadata"],
                submitted_code=submitted_code,
                language=exercise["metadata"].get("language", "Python"),
                experience_level=experience_level,
            )
        finally:
            end_api_logger(api_logger)

        self.manager.update_status(exercise_path, ExerciseManager.STATUS_REVIEWED)
        return RoguelikeSubmissionResult(
            exercise=exercise,
            review=review,
            model=model,
        )

    def reveal_next_hint(self, exercise_path: str) -> Dict[str, Any]:
        """Reveal next hint and return display metadata."""
        exercise = self.manager.get_exercise(exercise_path)
        if not exercise:
            raise ValueError(f"Exercise not found: {exercise_path}")

        metadata = exercise["metadata"]
        hints = metadata.get("solution_hints", [])
        revealed = metadata.get("hints_revealed", 0)

        hint = self.manager.get_next_hint(exercise_path)
        if metadata.get("status") == ExerciseManager.STATUS_PENDING:
            self.manager.update_status(exercise_path, ExerciseManager.STATUS_IN_PROGRESS)

        return {
            "hint": hint,
            "revealed_index": revealed + 1,
            "total_hints": len(hints),
            "remaining_hints": max(0, len(hints) - (revealed + 1)),
            "metadata": metadata,
        }

    def archive_run(self, exercise_path: str) -> bool:
        """Archive an exercise run."""
        return self.manager.archive_exercise(exercise_path)
