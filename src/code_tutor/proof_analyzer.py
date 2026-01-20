"""Proof analysis using Claude API."""

from typing import Dict, List, Optional, Any
import anthropic


class ProofAnalyzer:
    """Analyzes mathematical proofs using Claude API with educational approach."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-5"):
        """Initialize the proof analyzer.

        Args:
            api_key: Anthropic API key.
            model: Claude model to use.
        """
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.conversation_history: List[Dict[str, str]] = []

    def analyze_proof(
        self,
        content: str,
        file_metadata: Dict,
        structure: Dict,
        experience_level: str,
        domain: Optional[str] = None,
        preferences: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Perform initial proof analysis and generate clarifying questions.

        Args:
            content: Proof content to analyze.
            file_metadata: Metadata about the file.
            structure: Analyzed proof structure.
            experience_level: User's mathematical experience level.
            domain: Optional mathematical domain context.
            preferences: Optional user preferences.

        Returns:
            Dictionary with questions and initial observations.
        """
        prompt = self._build_initial_prompt(
            content, file_metadata, structure, experience_level, domain, preferences
        )

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
            )

            response_content = response.content[0].text

            # Store in conversation history
            self.conversation_history.append({"role": "user", "content": prompt})
            self.conversation_history.append({"role": "assistant", "content": response_content})

            return self._parse_initial_response(response_content)

        except Exception as e:
            raise ValueError(f"Failed to analyze proof: {e}")

    def process_answers(
        self,
        answers: List[str],
        experience_level: str,
        domain: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Process user's answers to questions and generate feedback.

        Args:
            answers: User's answers to the questions.
            experience_level: User's experience level.
            domain: Mathematical domain context.

        Returns:
            Dictionary with feedback and suggestions.
        """
        prompt = self._build_feedback_prompt(answers, experience_level, domain)

        try:
            self.conversation_history.append({"role": "user", "content": prompt})

            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=self.conversation_history,
            )

            response_content = response.content[0].text
            self.conversation_history.append({"role": "assistant", "content": response_content})

            return self._parse_feedback_response(response_content)

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

            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=self.conversation_history,
            )

            response_content = response.content[0].text
            self.conversation_history.append({"role": "assistant", "content": response_content})

            return response_content

        except Exception as e:
            raise ValueError(f"Failed to continue conversation: {e}")

    def _build_initial_prompt(
        self,
        content: str,
        file_metadata: Dict,
        structure: Dict,
        experience_level: str,
        domain: Optional[str],
        preferences: Optional[Dict],
    ) -> str:
        """Build the initial analysis prompt.

        Args:
            content: Proof content.
            file_metadata: File metadata.
            structure: Proof structure analysis.
            experience_level: User's experience level.
            domain: Mathematical domain.
            preferences: User preferences.

        Returns:
            Formatted prompt string.
        """
        experience_guidance = {
            "student": (
                "This person is learning to write proofs for the first time. "
                "Use clear language, explain proof techniques, and focus on logical structure. "
                "Be encouraging and patient with basic mistakes."
            ),
            "undergrad": (
                "This person is an undergraduate math student. They understand basic proof techniques "
                "but may struggle with more advanced concepts. Provide context for terminology."
            ),
            "graduate": (
                "This person is a graduate student. You can discuss sophisticated proof strategies, "
                "reference advanced theorems, and engage in nuanced discussions about rigor."
            ),
            "researcher": (
                "This person is an experienced mathematician. Engage at a professional level, "
                "discuss subtle points of rigor, and don't shy away from technical details."
            ),
        }

        domain_context = ""
        if domain:
            domain_context = f"\nMathematical Domain: {domain}"

        detected_domain = file_metadata.get("detected_domain", "")
        if detected_domain and not domain:
            domain_context = f"\nDetected Domain: {detected_domain} (auto-detected from content)"

        techniques_str = ", ".join(structure.get("proof_techniques", [])) or "Not detected"

        format_specific = ""
        if file_metadata.get("is_formal"):
            format_specific = """
Note: This is a formal proof in a proof assistant. Pay attention to:
- Type correctness and universe levels
- Proper use of tactics
- Completeness of the proof term
- Idiomatic use of the proof assistant's features"""

        return f"""You are a thoughtful, respectful mathematics tutor reviewing a proof. Your goal is to understand the proof's intent and approach before providing feedback.

Reviewer Profile:
- Experience Level: {experience_level}
- {experience_guidance.get(experience_level, experience_guidance['undergrad'])}
{domain_context}

Proof Information:
- Format: {file_metadata.get('format', 'Unknown')}
- Lines: {file_metadata.get('line_count', 0)}
- Has theorem statement: {structure.get('has_theorem_statement', False)}
- Has proof body: {structure.get('has_proof_body', False)}
- Detected techniques: {techniques_str}
{format_specific}

Proof to Review:
---
{content}
---

Your task:
1. Carefully read and understand the proof
2. Identify the main claim being proved
3. Trace the logical flow of the argument
4. Ask 2-4 thoughtful clarifying questions about:
   - The proof strategy and why it was chosen
   - Any steps that seem unclear or might benefit from more detail
   - Assumptions being made (stated or unstated)
   - The intended level of rigor

5. Provide brief initial observations (not criticism yet) about:
   - The overall structure and approach
   - Proof techniques being employed
   - Areas that might benefit from discussion

Format your response EXACTLY as follows:

## Main Claim
[One sentence describing what is being proved]

## Questions

1. [Your first question about the proof]
2. [Your second question]
3. [Your third question, if needed]

## Initial Observations

- [Observation 1]
- [Observation 2]
- [Observation 3]

Remember: Be respectful, assume the writer has good mathematical intuition, and focus on understanding their approach before judging its correctness or rigor."""

    def _build_feedback_prompt(
        self,
        answers: List[str],
        experience_level: str,
        domain: Optional[str],
    ) -> str:
        """Build the feedback prompt based on user answers.

        Args:
            answers: User's answers to questions.
            experience_level: User's experience level.
            domain: Mathematical domain.

        Returns:
            Formatted prompt string.
        """
        answers_text = "\n\n".join(
            f"Answer {i+1}: {answer}" for i, answer in enumerate(answers) if answer.strip()
        )

        return f"""Thank you for those answers. Now that I understand your proof strategy and intentions, let me provide constructive feedback.

User's Answers:
{answers_text}

Based on the mathematician's experience level ({experience_level}) and their explanations, please provide:

1. **Logical Correctness**: Evaluate the logical validity of the proof
   - Are all steps justified?
   - Are there any gaps in reasoning?
   - Are the assumptions valid and clearly stated?

2. **Rigor Assessment**: Comment on the level of rigor
   - Is the proof sufficiently rigorous for its intended audience?
   - Are there implicit assumptions that should be made explicit?
   - Are edge cases or special cases handled?

3. **Positive Feedback**: What's working well in this proof?
   - Good use of proof techniques
   - Clear exposition
   - Elegant steps or insights

4. **Suggestions for Improvement**: Concrete, actionable suggestions that:
   - Respect the proof's existing approach
   - Are appropriate for the experience level
   - Include brief explanations of WHY the suggestion helps
   - Provide specific examples when helpful

5. **Learning Opportunities**:
   - Related theorems or techniques worth exploring
   - Ways to strengthen or generalize the result
   - Common pitfalls in this type of proof

Format your response clearly with these sections. Be encouraging and educational.
Remember: A {experience_level} might need {'more explanation of fundamentals' if experience_level in ['student', 'undergrad'] else 'engagement with subtle points of rigor'}."""

    def _parse_initial_response(self, response: str) -> Dict[str, Any]:
        """Parse the initial analysis response.

        Args:
            response: Raw response from Claude.

        Returns:
            Parsed dictionary with questions and observations.
        """
        main_claim = ""
        questions = []
        observations = []

        lines = response.split("\n")
        current_section = None

        for line in lines:
            line_stripped = line.strip()

            if "## Main Claim" in line:
                current_section = "main_claim"
                continue
            elif "## Questions" in line or "## Question" in line:
                current_section = "questions"
                continue
            elif "## Initial Observations" in line or "## Observations" in line:
                current_section = "observations"
                continue
            elif line_stripped.startswith("##"):
                current_section = None
                continue

            if current_section == "main_claim" and line_stripped:
                main_claim = line_stripped
                current_section = None  # Only take first line
            elif current_section == "questions" and line_stripped:
                cleaned = line_stripped.lstrip("0123456789.)-) ").strip()
                if cleaned:
                    questions.append(cleaned)
            elif current_section == "observations" and line_stripped:
                cleaned = line_stripped.lstrip("*-•").strip()
                if cleaned:
                    observations.append(cleaned)

        return {
            "main_claim": main_claim,
            "questions": questions,
            "observations": observations,
            "raw_response": response,
        }

    def _parse_feedback_response(self, response: str) -> Dict[str, Any]:
        """Parse the feedback response.

        Args:
            response: Raw response from Claude.

        Returns:
            Parsed dictionary with feedback sections.
        """
        return {
            "feedback": response,
            "raw_response": response,
        }

    def reset_conversation(self):
        """Reset the conversation history."""
        self.conversation_history = []
