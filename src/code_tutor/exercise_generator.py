"""Exercise generation using Claude API."""

from typing import Dict, List, Optional, Any
import anthropic

from .exercise_manager import ExerciseManager


class ExerciseGenerator:
    """Generates coding exercises using Claude API."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-5"):
        """Initialize the exercise generator.

        Args:
            api_key: Anthropic API key.
            model: Claude model to use.
        """
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def generate_exercise(
        self,
        topic: str,
        language: str,
        exercise_type: str = ExerciseManager.TYPE_IMPLEMENTATION,
        difficulty: str = "intermediate",
        experience_level: str = "intermediate",
    ) -> Dict[str, Any]:
        """Generate an exercise on a given topic.

        Args:
            topic: The topic for the exercise.
            language: Programming language.
            exercise_type: Type of exercise to generate.
            difficulty: Difficulty level.
            experience_level: User's experience level.

        Returns:
            Dictionary with generated exercise content.
        """
        prompt = self._build_generation_prompt(
            topic, language, exercise_type, difficulty, experience_level
        )

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
            )

            content = response.content[0].text
            return self._parse_exercise_response(content)

        except Exception as e:
            raise ValueError(f"Failed to generate exercise: {e}")

    def _build_generation_prompt(
        self,
        topic: str,
        language: str,
        exercise_type: str,
        difficulty: str,
        experience_level: str,
    ) -> str:
        """Build the prompt for exercise generation.

        Args:
            topic: Exercise topic.
            language: Programming language.
            exercise_type: Type of exercise.
            difficulty: Difficulty level.
            experience_level: User's experience level.

        Returns:
            The prompt string.
        """
        type_instructions = {
            ExerciseManager.TYPE_FILL_IN: """
Create a code template with strategic blanks (marked with TODO comments) that the learner must fill in.
The blanks should test understanding of key concepts.
Include clear comments explaining what each blank should accomplish.""",

            ExerciseManager.TYPE_BUG_FIX: """
Create code that contains intentional bugs related to the topic.
The bugs should be instructive - common mistakes that teach important concepts.
Include a comment at the top explaining what the code SHOULD do.
Don't make the bugs obvious - they should require thinking.""",

            ExerciseManager.TYPE_IMPLEMENTATION: """
Provide a function/class signature with detailed docstrings explaining:
- What the function should do
- Input parameters and their types
- Expected return value and type
- Example inputs and outputs
The learner implements the entire body from scratch.""",

            ExerciseManager.TYPE_REFACTORING: """
Provide working but poorly structured code that accomplishes a task.
Issues might include: code duplication, poor naming, overly complex logic,
missing abstractions, or other code smells.
The learner should refactor while preserving functionality.""",

            ExerciseManager.TYPE_TEST_WRITING: """
Provide a complete implementation of a function/class.
The learner must write comprehensive tests that cover:
- Normal cases
- Edge cases
- Error conditions
Include a testing framework import appropriate for the language.""",
        }

        difficulty_guidance = {
            "beginner": "Use simple concepts, short code, and clear patterns. Focus on fundamentals.",
            "intermediate": "Include moderate complexity, common patterns, and some edge cases to consider.",
            "advanced": "Include complex scenarios, performance considerations, and subtle edge cases.",
            "expert": "Challenge with nuanced problems, architectural decisions, and optimization opportunities.",
        }

        return f"""You are an expert programming instructor creating a practice exercise.

Topic: {topic}
Language: {language}
Exercise Type: {exercise_type}
Difficulty: {difficulty}
Learner Level: {experience_level}

Difficulty Guidance: {difficulty_guidance.get(difficulty, difficulty_guidance['intermediate'])}

Exercise Type Instructions:
{type_instructions.get(exercise_type, type_instructions[ExerciseManager.TYPE_IMPLEMENTATION])}

Generate a complete exercise with the following format:

## Instructions
[Clear, detailed instructions for what the learner should do. Be specific about requirements and constraints. 2-4 paragraphs.]

## Learning Objectives
- [Objective 1 - what concept will they understand?]
- [Objective 2]
- [Objective 3]

## Starter Code
```{language.lower()}
[The code template/buggy code/signature that the learner will work with]
```

## Test Code
```{language.lower()}
[Optional but recommended: test cases the learner can run to verify their solution]
```

## Hints
1. [First hint - gentle nudge in the right direction]
2. [Second hint - more specific guidance]
3. [Third hint - nearly gives away the approach but not the answer]

## Solution Explanation
[Brief explanation of what the correct solution looks like and why - this will be hidden from the learner]

Remember:
- Make the exercise practical and relevant
- The starter code should be 15-50 lines depending on complexity
- Hints should progressively reveal more without giving away the answer
- Test code should be runnable if the learner has the standard testing framework"""

    def _parse_exercise_response(self, response: str) -> Dict[str, Any]:
        """Parse the exercise generation response.

        Args:
            response: Raw response from Claude.

        Returns:
            Parsed dictionary with exercise components.
        """
        sections = {
            "instructions": "",
            "learning_objectives": [],
            "starter_code": "",
            "test_code": "",
            "hints": [],
            "solution_explanation": "",
        }

        lines = response.split("\n")
        current_section = None
        in_code_block = False
        code_lines = []
        text_lines = []

        for line in lines:
            # Check for code block boundaries
            if line.strip().startswith("```"):
                if in_code_block:
                    # End of code block
                    if current_section == "starter_code":
                        sections["starter_code"] = "\n".join(code_lines)
                    elif current_section == "test_code":
                        sections["test_code"] = "\n".join(code_lines)
                    code_lines = []
                    in_code_block = False
                else:
                    # Start of code block
                    in_code_block = True
                continue

            if in_code_block:
                code_lines.append(line)
                continue

            # Check for section headers
            if line.strip().startswith("## Instructions"):
                if current_section and text_lines:
                    self._save_section(sections, current_section, text_lines)
                current_section = "instructions"
                text_lines = []
                continue
            elif line.strip().startswith("## Learning Objectives"):
                if current_section and text_lines:
                    self._save_section(sections, current_section, text_lines)
                current_section = "learning_objectives"
                text_lines = []
                continue
            elif line.strip().startswith("## Starter Code"):
                if current_section and text_lines:
                    self._save_section(sections, current_section, text_lines)
                current_section = "starter_code"
                text_lines = []
                continue
            elif line.strip().startswith("## Test Code"):
                if current_section and text_lines:
                    self._save_section(sections, current_section, text_lines)
                current_section = "test_code"
                text_lines = []
                continue
            elif line.strip().startswith("## Hints"):
                if current_section and text_lines:
                    self._save_section(sections, current_section, text_lines)
                current_section = "hints"
                text_lines = []
                continue
            elif line.strip().startswith("## Solution"):
                if current_section and text_lines:
                    self._save_section(sections, current_section, text_lines)
                current_section = "solution_explanation"
                text_lines = []
                continue

            # Collect text for current section
            if current_section and line.strip():
                text_lines.append(line)

        # Save final section
        if current_section and text_lines:
            self._save_section(sections, current_section, text_lines)

        return sections

    def _save_section(
        self, sections: Dict, section_name: str, lines: List[str]
    ) -> None:
        """Save collected lines to the appropriate section.

        Args:
            sections: Sections dictionary to update.
            section_name: Name of the section.
            lines: Lines collected for this section.
        """
        if section_name == "instructions":
            sections["instructions"] = "\n".join(lines)
        elif section_name == "learning_objectives":
            objectives = []
            for line in lines:
                cleaned = line.lstrip("*-•0123456789.) ").strip()
                if cleaned:
                    objectives.append(cleaned)
            sections["learning_objectives"] = objectives
        elif section_name == "hints":
            hints = []
            for line in lines:
                cleaned = line.lstrip("*-•0123456789.) ").strip()
                if cleaned:
                    hints.append(cleaned)
            sections["hints"] = hints
        elif section_name == "solution_explanation":
            sections["solution_explanation"] = "\n".join(lines)

    def review_submission(
        self,
        original_exercise: Dict[str, Any],
        submitted_code: str,
        language: str,
        experience_level: str = "intermediate",
    ) -> Dict[str, Any]:
        """Review a submitted exercise solution.

        Args:
            original_exercise: The original exercise metadata.
            submitted_code: The learner's submitted code.
            language: Programming language.
            experience_level: User's experience level.

        Returns:
            Dictionary with review feedback.
        """
        prompt = f"""You are reviewing a coding exercise submission from a {experience_level} programmer.

Exercise Topic: {original_exercise.get('topic', 'Unknown')}
Exercise Type: {original_exercise.get('exercise_type', 'Unknown')}
Learning Objectives:
{chr(10).join(f"- {obj}" for obj in original_exercise.get('learning_objectives', []))}

Submitted Code:
```{language.lower()}
{submitted_code}
```

Please provide a constructive review:

## Correctness
[Does the solution correctly address the exercise requirements? Are there any bugs or issues?]

## Code Quality
[Comment on style, readability, naming, and organization]

## Understanding Demonstrated
[Based on the solution, what concepts does the learner seem to understand well? What might need more practice?]

## Suggestions
[Specific, actionable suggestions for improvement]

## Overall Assessment
[NEEDS_WORK / ACCEPTABLE / GOOD / EXCELLENT]
[Brief summary of the submission quality]

Be encouraging but honest. Focus on learning and improvement."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}],
            )

            content = response.content[0].text

            # Parse assessment
            assessment = "ACCEPTABLE"
            for level in ["EXCELLENT", "GOOD", "ACCEPTABLE", "NEEDS_WORK"]:
                if level in content:
                    assessment = level
                    break

            return {
                "feedback": content,
                "assessment": assessment,
            }

        except Exception as e:
            raise ValueError(f"Failed to review submission: {e}")
