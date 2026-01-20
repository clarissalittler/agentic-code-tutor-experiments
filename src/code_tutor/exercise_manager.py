"""Exercise management for Code Tutor - working directory for practice exercises."""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import ConfigManager


class ExerciseManager:
    """Manages the exercise working directory and exercise lifecycle."""

    DEFAULT_EXERCISES_DIR = Path.home() / "code-tutor-exercises"
    METADATA_FILE = ".meta.json"
    README_FILE = "README.md"
    STARTER_FILE = "starter"

    # Exercise statuses
    STATUS_PENDING = "pending"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_SUBMITTED = "submitted"
    STATUS_REVIEWED = "reviewed"
    STATUS_ARCHIVED = "archived"

    # Exercise types
    TYPE_FILL_IN = "fill_in_blank"
    TYPE_BUG_FIX = "bug_fix"
    TYPE_IMPLEMENTATION = "implementation"
    TYPE_REFACTORING = "refactoring"
    TYPE_TEST_WRITING = "test_writing"

    EXERCISE_TYPES = [
        TYPE_FILL_IN,
        TYPE_BUG_FIX,
        TYPE_IMPLEMENTATION,
        TYPE_REFACTORING,
        TYPE_TEST_WRITING,
    ]

    # Language to file extension mapping
    LANGUAGE_EXTENSIONS = {
        "python": ".py",
        "javascript": ".js",
        "typescript": ".ts",
        "java": ".java",
        "c": ".c",
        "cpp": ".cpp",
        "c++": ".cpp",
        "go": ".go",
        "rust": ".rs",
        "ruby": ".rb",
        "php": ".php",
        "swift": ".swift",
        "kotlin": ".kt",
        "scala": ".scala",
        "shell": ".sh",
        "bash": ".sh",
        "sql": ".sql",
        "r": ".r",
    }

    def __init__(self, exercises_dir: Optional[Path] = None):
        """Initialize the exercise manager.

        Args:
            exercises_dir: Optional custom exercises directory path.
        """
        self.exercises_dir = exercises_dir or self.DEFAULT_EXERCISES_DIR

    def ensure_directory_exists(self) -> Path:
        """Ensure the exercises directory exists.

        Returns:
            Path to the exercises directory.
        """
        self.exercises_dir.mkdir(parents=True, exist_ok=True)
        return self.exercises_dir

    def get_exercise_path(self, exercise_id: str) -> Path:
        """Get the path to an exercise directory.

        Args:
            exercise_id: The exercise ID (directory name).

        Returns:
            Path to the exercise directory.
        """
        return self.exercises_dir / exercise_id

    def generate_exercise_id(self, topic: str) -> str:
        """Generate a unique exercise ID based on topic and timestamp.

        Args:
            topic: The exercise topic.

        Returns:
            A unique exercise ID.
        """
        # Sanitize topic for use in filename
        sanitized = topic.lower().replace(" ", "-")
        sanitized = "".join(c for c in sanitized if c.isalnum() or c == "-")
        sanitized = sanitized[:30]  # Limit length

        # Add timestamp for uniqueness
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

        return f"{sanitized}-{timestamp}"

    def get_file_extension(self, language: str) -> str:
        """Get file extension for a language.

        Args:
            language: Programming language name.

        Returns:
            File extension (including dot).
        """
        return self.LANGUAGE_EXTENSIONS.get(language.lower(), ".txt")

    def create_exercise(
        self,
        topic: str,
        language: str,
        exercise_type: str,
        difficulty: str,
        instructions: str,
        starter_code: str,
        solution_hints: List[str],
        learning_objectives: List[str],
        test_code: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new exercise in the working directory.

        Args:
            topic: The exercise topic.
            language: Programming language.
            exercise_type: Type of exercise (fill_in_blank, bug_fix, etc.).
            difficulty: Difficulty level (beginner, intermediate, advanced).
            instructions: Detailed instructions for the exercise.
            starter_code: The starter code template.
            solution_hints: List of hints for solving.
            learning_objectives: What the learner should understand after.
            test_code: Optional test code for self-checking.

        Returns:
            Dictionary with exercise info including path and ID.
        """
        self.ensure_directory_exists()

        # Generate unique ID
        exercise_id = self.generate_exercise_id(topic)
        exercise_path = self.get_exercise_path(exercise_id)

        # Create exercise directory
        exercise_path.mkdir(parents=True, exist_ok=True)

        # Create metadata
        metadata = {
            "id": exercise_id,
            "topic": topic,
            "language": language,
            "exercise_type": exercise_type,
            "difficulty": difficulty,
            "status": self.STATUS_PENDING,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "learning_objectives": learning_objectives,
            "solution_hints": solution_hints,
            "hints_revealed": 0,
        }

        # Write metadata
        metadata_path = exercise_path / self.METADATA_FILE
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

        # Create README
        readme_content = self._generate_readme(
            topic, language, exercise_type, difficulty, instructions, learning_objectives
        )
        readme_path = exercise_path / self.README_FILE
        with open(readme_path, "w") as f:
            f.write(readme_content)

        # Create starter file
        extension = self.get_file_extension(language)
        starter_path = exercise_path / f"{self.STARTER_FILE}{extension}"
        with open(starter_path, "w") as f:
            f.write(starter_code)

        # Create test file if provided
        if test_code:
            test_path = exercise_path / f"test_exercise{extension}"
            with open(test_path, "w") as f:
                f.write(test_code)

        return {
            "id": exercise_id,
            "path": str(exercise_path),
            "metadata": metadata,
            "files": {
                "readme": str(readme_path),
                "starter": str(starter_path),
                "test": str(exercise_path / f"test_exercise{extension}") if test_code else None,
            },
        }

    def _generate_readme(
        self,
        topic: str,
        language: str,
        exercise_type: str,
        difficulty: str,
        instructions: str,
        learning_objectives: List[str],
    ) -> str:
        """Generate README content for an exercise.

        Args:
            topic: Exercise topic.
            language: Programming language.
            exercise_type: Type of exercise.
            difficulty: Difficulty level.
            instructions: Exercise instructions.
            learning_objectives: Learning objectives.

        Returns:
            README markdown content.
        """
        objectives_list = "\n".join(f"- {obj}" for obj in learning_objectives)

        type_descriptions = {
            self.TYPE_FILL_IN: "Complete the missing parts of the code",
            self.TYPE_BUG_FIX: "Find and fix the bug(s) in the code",
            self.TYPE_IMPLEMENTATION: "Implement the function/class from scratch",
            self.TYPE_REFACTORING: "Refactor the code to be cleaner/more efficient",
            self.TYPE_TEST_WRITING: "Write tests for the provided implementation",
        }

        return f"""# Exercise: {topic}

**Language:** {language}
**Type:** {type_descriptions.get(exercise_type, exercise_type)}
**Difficulty:** {difficulty.capitalize()}

## Learning Objectives

{objectives_list}

## Instructions

{instructions}

## Getting Started

1. Open the `starter{self.get_file_extension(language)}` file
2. Read through the code and comments carefully
3. Complete the exercise according to the instructions above
4. When done, run `code-tutor exercise submit {self.exercises_dir.name}/{topic}` to get feedback

## Need Help?

- Run `code-tutor exercise hint <path>` to get a hint
- Hints are revealed progressively - try to solve it first!

---
*Generated by Code Tutor*
"""

    def list_exercises(
        self, status_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List all exercises in the working directory.

        Args:
            status_filter: Optional status to filter by.

        Returns:
            List of exercise info dictionaries.
        """
        if not self.exercises_dir.exists():
            return []

        exercises = []

        for item in self.exercises_dir.iterdir():
            if item.is_dir():
                metadata_path = item / self.METADATA_FILE
                if metadata_path.exists():
                    try:
                        with open(metadata_path, "r") as f:
                            metadata = json.load(f)

                        if status_filter and metadata.get("status") != status_filter:
                            continue

                        exercises.append({
                            "id": item.name,
                            "path": str(item),
                            "metadata": metadata,
                        })
                    except (json.JSONDecodeError, IOError):
                        continue

        # Sort by creation date, newest first
        exercises.sort(
            key=lambda x: x["metadata"].get("created_at", ""),
            reverse=True
        )

        return exercises

    def get_exercise(self, exercise_id_or_path: str) -> Optional[Dict[str, Any]]:
        """Get a specific exercise by ID or path.

        Args:
            exercise_id_or_path: Exercise ID or full path.

        Returns:
            Exercise info dictionary or None if not found.
        """
        # Try as path first
        path = Path(exercise_id_or_path)
        if not path.is_absolute():
            # Try as ID
            path = self.exercises_dir / exercise_id_or_path

        if not path.exists():
            return None

        metadata_path = path / self.METADATA_FILE
        if not metadata_path.exists():
            return None

        try:
            with open(metadata_path, "r") as f:
                metadata = json.load(f)

            # Find starter file
            starter_file = None
            for item in path.iterdir():
                if item.name.startswith("starter"):
                    starter_file = str(item)
                    break

            return {
                "id": path.name,
                "path": str(path),
                "metadata": metadata,
                "starter_file": starter_file,
            }
        except (json.JSONDecodeError, IOError):
            return None

    def update_status(self, exercise_id_or_path: str, new_status: str) -> bool:
        """Update the status of an exercise.

        Args:
            exercise_id_or_path: Exercise ID or path.
            new_status: New status to set.

        Returns:
            True if successful, False otherwise.
        """
        exercise = self.get_exercise(exercise_id_or_path)
        if not exercise:
            return False

        metadata_path = Path(exercise["path"]) / self.METADATA_FILE

        try:
            exercise["metadata"]["status"] = new_status
            exercise["metadata"]["updated_at"] = datetime.now().isoformat()

            with open(metadata_path, "w") as f:
                json.dump(exercise["metadata"], f, indent=2)

            return True
        except IOError:
            return False

    def get_next_hint(self, exercise_id_or_path: str) -> Optional[str]:
        """Get the next hint for an exercise.

        Args:
            exercise_id_or_path: Exercise ID or path.

        Returns:
            The next hint string or None if no more hints.
        """
        exercise = self.get_exercise(exercise_id_or_path)
        if not exercise:
            return None

        metadata = exercise["metadata"]
        hints = metadata.get("solution_hints", [])
        revealed = metadata.get("hints_revealed", 0)

        if revealed >= len(hints):
            return None

        # Update hints revealed count
        metadata["hints_revealed"] = revealed + 1
        metadata["updated_at"] = datetime.now().isoformat()

        metadata_path = Path(exercise["path"]) / self.METADATA_FILE
        try:
            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)
        except IOError:
            pass

        return hints[revealed]

    def get_starter_code(self, exercise_id_or_path: str) -> Optional[str]:
        """Read the starter code for an exercise.

        Args:
            exercise_id_or_path: Exercise ID or path.

        Returns:
            The starter code content or None if not found.
        """
        exercise = self.get_exercise(exercise_id_or_path)
        if not exercise or not exercise.get("starter_file"):
            return None

        try:
            with open(exercise["starter_file"], "r") as f:
                return f.read()
        except IOError:
            return None

    def archive_exercise(self, exercise_id_or_path: str) -> bool:
        """Archive an exercise (move to archived subdirectory).

        Args:
            exercise_id_or_path: Exercise ID or path.

        Returns:
            True if successful, False otherwise.
        """
        exercise = self.get_exercise(exercise_id_or_path)
        if not exercise:
            return False

        archive_dir = self.exercises_dir / "archived"
        archive_dir.mkdir(exist_ok=True)

        source = Path(exercise["path"])
        dest = archive_dir / source.name

        try:
            shutil.move(str(source), str(dest))
            return True
        except (shutil.Error, IOError):
            return False

    def delete_exercise(self, exercise_id_or_path: str) -> bool:
        """Permanently delete an exercise.

        Args:
            exercise_id_or_path: Exercise ID or path.

        Returns:
            True if successful, False otherwise.
        """
        exercise = self.get_exercise(exercise_id_or_path)
        if not exercise:
            return False

        try:
            shutil.rmtree(exercise["path"])
            return True
        except (shutil.Error, IOError):
            return False
