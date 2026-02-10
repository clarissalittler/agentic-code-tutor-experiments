"""Code analysis using pluggable LLM providers."""

from typing import Any, Dict, List, Optional

from .logger import SessionLogger
from .llm_provider import LLMClient, create_llm_client
from .models import CodeFeedbackResult, CodeInitialAnalysisResult
from .response_parsing import (
    extract_json_object,
    parse_string_list,
)


class CodeAnalyzer:
    """Analyzes code using LLM APIs with educational, respectful approach."""

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-5",
        provider: str = "anthropic",
        base_url: Optional[str] = None,
        logger: Optional[SessionLogger] = None,
        log_api_calls: bool = False,
    ):
        """Initialize the code analyzer.

        Args:
            api_key: Provider API key.
            model: Model to use.
            provider: LLM provider name.
            base_url: Optional custom API base URL.
            logger: Optional session logger for API call logging.
            log_api_calls: Whether to log API calls.
        """
        self.client: LLMClient = create_llm_client(
            provider=provider,
            api_key=api_key,
            base_url=base_url,
        )
        self.model = model
        self.conversation_history: List[Dict[str, str]] = []
        self.logger = logger
        self.log_api_calls = log_api_calls

    def analyze_code(
        self,
        code: str,
        file_metadata: Dict,
        experience_level: str,
        preferences: Dict,
    ) -> CodeInitialAnalysisResult:
        """Perform initial code analysis and generate clarifying questions.

        Args:
            code: Source code to analyze.
            file_metadata: Metadata about the file (language, size, etc.).
            experience_level: User's programming experience level.
            preferences: User preferences (question_style, focus_areas, etc.).

        Returns:
            Structured analysis result with questions and observations.
        """
        prompt = self._build_initial_prompt(code, file_metadata, experience_level, preferences)

        try:
            completion = self.client.complete_with_metadata(
                model=self.model,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
            )
            content = completion.text

            # Store in conversation history
            self.conversation_history.append({"role": "user", "content": prompt})
            self.conversation_history.append({"role": "assistant", "content": content})
            self._log_api_call(prompt, content, completion.usage)

            return self._parse_initial_response(content)

        except Exception as e:
            raise ValueError(f"Failed to analyze code: {e}")

    def process_answers(
        self,
        answers: List[str],
        experience_level: str,
        preferences: Dict,
    ) -> CodeFeedbackResult:
        """Process user's answers to questions and generate feedback.

        Args:
            answers: User's answers to the questions.
            experience_level: User's programming experience level.
            preferences: User preferences.

        Returns:
            Structured feedback result.
        """
        prompt = self._build_feedback_prompt(answers, experience_level, preferences)

        try:
            # Add the answers to conversation history
            self.conversation_history.append({"role": "user", "content": prompt})

            completion = self.client.complete_with_metadata(
                model=self.model,
                max_tokens=4096,
                messages=self.conversation_history,
            )
            content = completion.text

            # Store response in history
            self.conversation_history.append({"role": "assistant", "content": content})
            self._log_api_call(prompt, content, completion.usage)

            return self._parse_feedback_response(content)

        except Exception as e:
            raise ValueError(f"Failed to process answers: {e}")

    def continue_conversation(self, user_message: str) -> str:
        """Continue the conversation with a follow-up question.

        Args:
            user_message: User's follow-up question or comment.

        Returns:
            Assistant's response.
        """
        try:
            self.conversation_history.append({"role": "user", "content": user_message})

            completion = self.client.complete_with_metadata(
                model=self.model,
                max_tokens=4096,
                messages=self.conversation_history,
            )
            content = completion.text
            self.conversation_history.append({"role": "assistant", "content": content})
            self._log_api_call(user_message, content, completion.usage)

            return content

        except Exception as e:
            raise ValueError(f"Failed to continue conversation: {e}")

    def _log_api_call(
        self,
        prompt: str,
        response: str,
        usage: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log an API call if logging is enabled."""
        if self.logger and self.log_api_calls:
            self.logger.log_api_call(self.model, prompt, response, usage=usage)

    def _build_initial_prompt(
        self,
        code: str,
        file_metadata: Dict,
        experience_level: str,
        preferences: Dict,
    ) -> str:
        """Build the initial analysis prompt.

        Args:
            code: Source code.
            file_metadata: File metadata.
            experience_level: User's experience level.
            preferences: User preferences.

        Returns:
            Formatted prompt string.
        """
        focus_areas_str = ", ".join(preferences.get("focus_areas", ["design", "readability"]))
        question_style = preferences.get("question_style", "socratic")

        style_guidance = {
            "socratic": "Ask questions that lead the learner to discover insights themselves.",
            "direct": "Ask straightforward, specific questions about the code.",
            "exploratory": "Ask open-ended questions about alternatives and trade-offs.",
        }

        experience_guidance = {
            "beginner": (
                "This programmer is learning. Use clear language, explain concepts, "
                "and focus on fundamentals. Avoid jargon unless you explain it."
            ),
            "intermediate": (
                "This programmer has some experience. You can discuss trade-offs and "
                "introduce more advanced concepts, but provide context."
            ),
            "advanced": (
                "This programmer is experienced. Focus on architecture, design patterns, "
                "and deeper implications. You can reference advanced concepts."
            ),
            "expert": (
                "This programmer is highly skilled. Engage in nuanced discussions about "
                "design philosophy, performance implications, and best practices."
            ),
        }

        return f"""You are a respectful, thoughtful code tutor. Your goal is to understand the programmer's code before providing feedback.

Programmer Profile:
- Experience Level: {experience_level}
- {experience_guidance.get(experience_level, experience_guidance['intermediate'])}
- Preferred Focus Areas: {focus_areas_str}
- Question Style: {question_style}
- {style_guidance.get(question_style, style_guidance['socratic'])}

File Information:
- Language: {file_metadata.get('language', 'Unknown')}
- Lines of Code: {file_metadata.get('line_count', 0)}
- File: {file_metadata.get('name', 'unknown')}

Code to Review:
```{file_metadata.get('language', '').lower()}
{code}
```

Your task:
1. Carefully read and understand the code
2. Ask 2-4 thoughtful clarifying questions about:
   - Design decisions and their rationale
   - Intended use cases or constraints
   - Any patterns or choices that seem intentional
   - Trade-offs the programmer considered

        3. Provide brief initial observations (not criticism) about:
   - Overall structure and organization
   - Notable patterns or approaches used
   - Areas that might benefit from discussion

Return ONLY valid JSON (no markdown, no prose) with this schema:
{{
  "questions": ["question 1", "question 2", "question 3"],
  "observations": ["observation 1", "observation 2", "observation 3"]
}}

Remember:
- Ask 2-4 questions.
- Keep observations brief and neutral.
- Be respectful, assume good intentions, and focus on understanding before judging."""

    def _build_feedback_prompt(
        self,
        answers: List[str],
        experience_level: str,
        preferences: Dict,
    ) -> str:
        """Build the feedback prompt based on user answers.

        Args:
            answers: User's answers to questions.
            experience_level: User's experience level.
            preferences: User preferences.

        Returns:
            Formatted prompt string.
        """
        answers_text = "\n\n".join(
            f"Answer {i+1}: {answer}" for i, answer in enumerate(answers) if answer.strip()
        )

        return f"""Thank you for those answers. Now that I understand your intentions and reasoning, let me provide constructive feedback.

User's Answers:
{answers_text}

Based on the programmer's experience level ({experience_level}) and their explanations, please provide:

1. **Positive Feedback**: What's working well? What shows good understanding or thoughtful decisions?

2. **Suggestions for Improvement**: Concrete, actionable suggestions that:
   - Respect the programmer's existing style and intentions
   - Align with their experience level
   - Include brief explanations of WHY the suggestion helps
   - Provide examples when helpful

3. **Learning Opportunities**: Concepts, patterns, or techniques worth exploring further

4. **Trade-offs Discussion**: Any interesting trade-offs in their current approach

Format your response clearly with these sections. Be encouraging and educational, not critical.
Remember their focus areas: {', '.join(preferences.get('focus_areas', ['general']))}.

Keep your feedback concise but meaningful. For a {experience_level} programmer, adjust your explanations accordingly."""

    def _parse_initial_response(self, response: str) -> CodeInitialAnalysisResult:
        """Parse the initial analysis response.

        Args:
            response: Raw response from Claude.

        Returns:
            Parsed initial analysis result.
        """
        parsed_json = extract_json_object(response)
        if parsed_json is not None:
            questions = parse_string_list(parsed_json, "questions")
            observations = parse_string_list(parsed_json, "observations")
            if questions or observations:
                return CodeInitialAnalysisResult(
                    questions=questions,
                    observations=observations,
                    raw_response=response,
                )

        return self._parse_markdown_initial_response(response)

    def _parse_markdown_initial_response(self, response: str) -> CodeInitialAnalysisResult:
        """Fallback parser for legacy heading/list formatted responses."""
        questions = []
        observations = []

        lines = response.split("\n")
        current_section = None

        for line in lines:
            line = line.strip()

            if "## Questions" in line or "## Question" in line:
                current_section = "questions"
                continue
            elif "## Initial Observations" in line or "## Observations" in line:
                current_section = "observations"
                continue
            elif line.startswith("##"):
                current_section = None
                continue

            if current_section == "questions" and line:
                # Remove numbering like "1. " or "1) "
                cleaned = line.lstrip("0123456789.)-) ").strip()
                if cleaned:
                    questions.append(cleaned)
            elif current_section == "observations" and line:
                # Remove bullet points
                cleaned = line.lstrip("*-•").strip()
                if cleaned:
                    observations.append(cleaned)

        return CodeInitialAnalysisResult(
            questions=questions,
            observations=observations,
            raw_response=response,
        )

    def _parse_feedback_response(self, response: str) -> CodeFeedbackResult:
        """Parse the feedback response.

        Args:
            response: Raw response from Claude.

        Returns:
            Parsed feedback result.
        """
        # For now, return the raw response
        # Could be enhanced to parse into sections
        return CodeFeedbackResult(
            feedback=response,
            raw_response=response,
        )

    def reset_conversation(self):
        """Reset the conversation history."""
        self.conversation_history = []
