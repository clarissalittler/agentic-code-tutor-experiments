"""
Code analysis using Claude API.

📚 FILE OVERVIEW:
This file integrates with Anthropic's Claude AI to analyze code and provide
educational feedback. It's the "brain" of the application - where all the AI
interaction happens. This is one of the most complex files in the project.

🎯 WHAT YOU'LL LEARN:
- How to integrate with the Anthropic Claude API
- Prompt engineering techniques for code analysis
- Managing conversation history for multi-turn dialogue
- Parsing structured responses from LLMs
- Building sophisticated prompts with context
- Error handling for API calls

💡 WHY THIS FILE EXISTS:
The Claude API requires:
1. Proper authentication and configuration
2. Well-crafted prompts to get good results
3. Conversation history tracking for context
4. Response parsing to extract structured data

This class wraps all that complexity in a clean API.
"""

# ============================================================================
# IMPORTS
# ============================================================================

from typing import Dict, List, Optional  # 💡 Type hints for clarity
import anthropic  # 🔍 Official Anthropic Python SDK for Claude API


# ============================================================================
# CodeAnalyzer CLASS
# ============================================================================

class CodeAnalyzer:
    """
    Analyzes code using Claude API with educational, respectful approach.

    🔍 DESIGN PATTERN: Facade Pattern
    This class provides a simplified interface to the complex Claude API.
    Instead of dealing with API details directly, other code can just call
    simple methods like analyze_code() and process_answers().

    💡 KEY RESPONSIBILITIES:
    1. Manage Claude API client and authentication
    2. Build sophisticated prompts for code analysis
    3. Maintain conversation history for context
    4. Parse structured responses from Claude
    5. Handle API errors gracefully

    🎯 CONVERSATION FLOW:
    1. analyze_code() - Initial analysis, generates questions
    2. process_answers() - Feedback based on user's answers
    3. continue_conversation() - Follow-up Q&A (optional, can repeat)
    """

    # ------------------------------------------------------------------------
    # INITIALIZATION
    # ------------------------------------------------------------------------

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-5"):
        """
        Initialize the code analyzer.

        🔍 WHAT HAPPENS HERE:
        1. Create Anthropic API client with credentials
        2. Store model name for future API calls
        3. Initialize empty conversation history

        💡 CONVERSATION HISTORY:
        The conversation_history list stores all messages exchanged with Claude.
        This allows Claude to have context about previous exchanges, enabling
        coherent multi-turn conversations.

        Args:
            api_key: Anthropic API key (from config).
            model: Claude model to use (default: claude-sonnet-4-5).
                  Options: "claude-sonnet-4-5" (balanced) or
                          "claude-haiku-4-5" (faster, cheaper)
        """
        # Initialize the Anthropic client
        # 🎯 This handles authentication and connection details
        self.client = anthropic.Anthropic(api_key=api_key)

        # Store which model to use
        self.model = model

        # Initialize conversation history
        # 🔍 Format: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
        # This follows OpenAI/Anthropic message format standard
        self.conversation_history: List[Dict[str, str]] = []

    # ------------------------------------------------------------------------
    # INITIAL CODE ANALYSIS
    # ------------------------------------------------------------------------

    def analyze_code(
        self,
        code: str,
        file_metadata: Dict,
        experience_level: str,
        preferences: Dict,
    ) -> Dict[str, any]:
        """
        Perform initial code analysis and generate clarifying questions.

        🔍 THIS IS THE FIRST STEP in the analysis workflow.

        💡 WHAT IT DOES:
        1. Build a detailed prompt with code, metadata, and user preferences
        2. Send to Claude API
        3. Parse response to extract questions and observations
        4. Store conversation in history for future context

        🎯 WHY ASK QUESTIONS FIRST:
        Rather than immediately criticizing code, we ask about design decisions.
        This is more respectful and leads to better feedback because we understand
        the programmer's intentions and constraints.

        Args:
            code: Source code to analyze (the actual file contents).
            file_metadata: Metadata about the file (language, size, etc.).
            experience_level: User's programming experience (beginner/intermediate/advanced/expert).
            preferences: User preferences (question_style, focus_areas, etc.).

        Returns:
            Dictionary with:
            {
                "questions": ["Question 1?", "Question 2?", ...],
                "observations": ["Observation 1", "Observation 2", ...],
                "raw_response": "Full text response from Claude"
            }

        Example:
            >>> analyzer = CodeAnalyzer(api_key="...")
            >>> result = analyzer.analyze_code(
            ...     code="def hello():\\n    print('hi')",
            ...     file_metadata={"language": "Python", "line_count": 2},
            ...     experience_level="intermediate",
            ...     preferences={"question_style": "socratic"}
            ... )
            >>> print(result["questions"])
            ["What was your intention with this function?", ...]
        """
        # Build the prompt (see _build_initial_prompt for details)
        prompt = self._build_initial_prompt(code, file_metadata, experience_level, preferences)

        try:
            # ========================================
            # MAKE API CALL TO CLAUDE
            # ========================================
            # 🔍 This is where we actually talk to Claude

            response = self.client.messages.create(
                model=self.model,  # Which Claude model to use
                max_tokens=4096,   # Maximum response length (4096 tokens ≈ 3000 words)
                messages=[{"role": "user", "content": prompt}],  # Our prompt as user message
            )

            # Extract text from response
            # 🎯 Response format: response.content is a list of content blocks
            # We take the first one (index 0) and get its text
            content = response.content[0].text

            # ========================================
            # STORE IN CONVERSATION HISTORY
            # ========================================
            # 💡 This allows future messages to have context

            # Add our prompt
            self.conversation_history.append({"role": "user", "content": prompt})
            # Add Claude's response
            self.conversation_history.append({"role": "assistant", "content": content})

            # ========================================
            # PARSE AND RETURN
            # ========================================
            # Extract structured data from the text response
            return self._parse_initial_response(content)

        except Exception as e:
            # ⚠️ API calls can fail for many reasons:
            # - Network issues
            # - Invalid API key
            # - Rate limiting
            # - Service outage
            raise ValueError(f"Failed to analyze code: {e}")

    # ------------------------------------------------------------------------
    # PROCESS USER'S ANSWERS
    # ------------------------------------------------------------------------

    def process_answers(
        self,
        answers: List[str],
        experience_level: str,
        preferences: Dict,
    ) -> Dict[str, any]:
        """
        Process user's answers to questions and generate feedback.

        🔍 THIS IS THE SECOND STEP - after we've asked questions and gotten answers.

        💡 NOW THAT WE UNDERSTAND THE USER'S INTENTIONS:
        We can provide personalized, respectful feedback that considers:
        - Why they made certain decisions
        - What constraints they were working with
        - Their experience level
        - Their focus areas

        🎯 USES CONVERSATION HISTORY:
        Because we stored the previous exchange in conversation_history,
        Claude remembers:
        - The original code
        - The questions we asked
        - The context from the initial analysis

        Args:
            answers: User's answers to the questions (list of strings).
            experience_level: User's programming experience level.
            preferences: User preferences.

        Returns:
            Dictionary with:
            {
                "feedback": "Markdown-formatted feedback",
                "raw_response": "Full text response"
            }

        Example:
            >>> # After analyze_code():
            >>> result = analyzer.process_answers(
            ...     answers=["I chose this approach because...", "..."],
            ...     experience_level="intermediate",
            ...     preferences={"focus_areas": ["design", "readability"]}
            ... )
            >>> print(result["feedback"])  # Personalized feedback based on answers
        """
        # Build prompt requesting feedback based on answers
        prompt = self._build_feedback_prompt(answers, experience_level, preferences)

        try:
            # Add the answers to conversation history
            # 💡 This creates a full conversation thread Claude can reference
            self.conversation_history.append({"role": "user", "content": prompt})

            # ========================================
            # MAKE API CALL WITH FULL HISTORY
            # ========================================
            # 🔍 Note: We pass the ENTIRE conversation_history, not just this prompt
            # This gives Claude full context of the conversation so far

            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=self.conversation_history,  # Full conversation, not just current prompt!
            )

            content = response.content[0].text

            # Store Claude's feedback in history
            self.conversation_history.append({"role": "assistant", "content": content})

            # Parse and return
            return self._parse_feedback_response(content)

        except Exception as e:
            raise ValueError(f"Failed to process answers: {e}")

    # ------------------------------------------------------------------------
    # CONTINUE CONVERSATION
    # ------------------------------------------------------------------------

    def continue_conversation(self, user_message: str) -> str:
        """
        Continue the conversation with a follow-up question.

        🔍 THIS IS OPTIONAL - for follow-up questions after feedback.

        💡 USE CASE:
        User might want to:
        - Ask for clarification on feedback
        - Discuss specific suggestions
        - Ask about alternative approaches
        - Request examples

        🎯 MAINTAINS FULL CONTEXT:
        Because conversation_history includes all previous messages,
        Claude remembers everything discussed so far.

        Args:
            user_message: User's follow-up question or comment.

        Returns:
            Assistant's response (string).

        Example:
            >>> response = analyzer.continue_conversation(
            ...     "Can you explain more about the performance concern you mentioned?"
            ... )
            >>> print(response)  # Claude's explanation
        """
        try:
            # Add user's message to history
            self.conversation_history.append({"role": "user", "content": user_message})

            # Get Claude's response with full context
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=self.conversation_history,  # Full conversation context
            )

            content = response.content[0].text

            # Store response in history
            self.conversation_history.append({"role": "assistant", "content": content})

            # Return raw text (no parsing needed for follow-up)
            return content

        except Exception as e:
            raise ValueError(f"Failed to continue conversation: {e}")

    # ========================================================================
    # PROMPT BUILDING METHODS
    # ========================================================================
    # 💡 These methods create the prompts sent to Claude
    # 🔍 PROMPT ENGINEERING is an art - these are carefully crafted!

    def _build_initial_prompt(
        self,
        code: str,
        file_metadata: Dict,
        experience_level: str,
        preferences: Dict,
    ) -> str:
        """
        Build the initial analysis prompt.

        🔍 THIS IS THE HEART OF THE APPLICATION - the prompt design!

        💡 PROMPT ENGINEERING TECHNIQUES USED:
        1. **Role Assignment**: "You are a respectful, thoughtful code tutor"
        2. **Context Provision**: Experience level, preferences, file info
        3. **Clear Instructions**: Numbered steps, specific requirements
        4. **Example Format**: Shows exactly how to format response
        5. **Tone Setting**: "Be respectful, assume good intentions"

        🎯 WHY THIS STRUCTURE WORKS:
        - Gives Claude a clear persona (respectful tutor)
        - Provides all context needed for personalized feedback
        - Specifies exact output format (## Questions, ## Observations)
        - Sets the right tone (educational, not critical)

        Args:
            code: Source code.
            file_metadata: File metadata.
            experience_level: User's experience level.
            preferences: User preferences.

        Returns:
            Formatted prompt string.
        """
        # Extract preferences
        focus_areas_str = ", ".join(preferences.get("focus_areas", ["design", "readability"]))
        question_style = preferences.get("question_style", "socratic")

        # ------------------------
        # STYLE GUIDANCE
        # ------------------------
        # 💡 Different questioning approaches for different learning styles
        style_guidance = {
            "socratic": "Ask questions that lead the learner to discover insights themselves.",
            "direct": "Ask straightforward, specific questions about the code.",
            "exploratory": "Ask open-ended questions about alternatives and trade-offs.",
        }

        # ------------------------
        # EXPERIENCE LEVEL GUIDANCE
        # ------------------------
        # 🎯 Tailor language and concepts to user's skill level
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

        # ========================================
        # BUILD THE PROMPT
        # ========================================
        # 🔍 F-string with triple quotes for multi-line formatted string
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

Format your response EXACTLY as follows:

## Questions

1. [Your first question]
2. [Your second question]
3. [Your third question, if needed]

## Initial Observations

- [Observation 1]
- [Observation 2]
- [Observation 3]

Remember: Be respectful, assume good intentions, and focus on understanding before judging."""

    def _build_feedback_prompt(
        self,
        answers: List[str],
        experience_level: str,
        preferences: Dict,
    ) -> str:
        """
        Build the feedback prompt based on user answers.

        💡 THIS PROMPT ASKS CLAUDE TO PROVIDE FEEDBACK NOW THAT WE
        UNDERSTAND THE USER'S REASONING.

        🎯 STRUCTURE OF FEEDBACK REQUESTED:
        1. Positive Feedback - What's working well?
        2. Suggestions for Improvement - Actionable, respectful suggestions
        3. Learning Opportunities - Concepts to explore further
        4. Trade-offs Discussion - Interesting design trade-offs

        Args:
            answers: User's answers to questions.
            experience_level: User's experience level.
            preferences: User preferences.

        Returns:
            Formatted prompt string.
        """
        # Format answers into a readable text block
        # 💡 enumerate(answers, 1) starts counting at 1, not 0
        answers_text = "\n\n".join(
            f"Answer {i+1}: {answer}" for i, answer in enumerate(answers) if answer.strip()
        )

        # Build the feedback request prompt
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

    # ========================================================================
    # RESPONSE PARSING METHODS
    # ========================================================================
    # 💡 Extract structured data from Claude's text responses

    def _parse_initial_response(self, response: str) -> Dict[str, any]:
        """
        Parse the initial analysis response.

        🔍 LLM CHALLENGE: Structured Data Extraction
        Claude returns unstructured text. We need to extract:
        - List of questions
        - List of observations
        We do this by looking for section markers (## Questions, ## Observations)

        💡 PARSING STRATEGY:
        1. Split response into lines
        2. Track which section we're in (questions or observations)
        3. Extract items from each section
        4. Clean up formatting (remove numbering, bullets)

        Args:
            response: Raw response from Claude.

        Returns:
            Parsed dictionary with questions and observations.
        """
        questions = []
        observations = []

        lines = response.split("\n")
        current_section = None  # Track which section we're in

        for line in lines:
            line = line.strip()

            # ========================================
            # DETECT SECTION HEADERS
            # ========================================
            # 🔍 Look for ## Questions or ## Observations

            if "## Questions" in line or "## Question" in line:
                current_section = "questions"
                continue  # Skip to next line (don't process header itself)

            elif "## Initial Observations" in line or "## Observations" in line:
                current_section = "observations"
                continue

            elif line.startswith("##"):
                # Different section - stop extracting
                current_section = None
                continue

            # ========================================
            # EXTRACT ITEMS FROM CURRENT SECTION
            # ========================================

            if current_section == "questions" and line:
                # Remove numbering like "1. ", "2) ", etc.
                # 🎯 lstrip removes specified characters from left side
                cleaned = line.lstrip("0123456789.)-) ").strip()
                if cleaned:
                    questions.append(cleaned)

            elif current_section == "observations" and line:
                # Remove bullet points like "- ", "* ", "• "
                cleaned = line.lstrip("*-•").strip()
                if cleaned:
                    observations.append(cleaned)

        return {
            "questions": questions,
            "observations": observations,
            "raw_response": response,  # Keep full response for debugging
        }

    def _parse_feedback_response(self, response: str) -> Dict[str, any]:
        """
        Parse the feedback response.

        💡 SIMPLER THAN INITIAL PARSE:
        Feedback is already well-structured markdown. We don't need to
        parse it into pieces - just return it as-is for rendering.

        🔍 COULD BE ENHANCED:
        Future versions could parse this into sections:
        - Positive feedback
        - Suggestions
        - Learning opportunities
        - Trade-offs
        But for now, returning raw markdown works well with Rich's renderer.

        Args:
            response: Raw response from Claude.

        Returns:
            Parsed dictionary with feedback sections.
        """
        # For now, return the raw response
        # 💡 Rich library can render markdown directly, so no parsing needed
        return {
            "feedback": response,
            "raw_response": response,
        }

    # ------------------------------------------------------------------------
    # UTILITY METHODS
    # ------------------------------------------------------------------------

    def reset_conversation(self):
        """
        Reset the conversation history.

        💡 USE CASE: When starting a new file review
        You want to clear previous context so Claude doesn't mix up
        different files.

        🎯 SIMPLY CLEARS THE HISTORY LIST
        """
        self.conversation_history = []


# ============================================================================
# KEY TAKEAWAYS
# ============================================================================
"""
🎓 WHAT YOU LEARNED:

1. **API Integration**
   - Use official SDK (anthropic) for reliability
   - Initialize client with API key
   - Handle authentication and errors

2. **Conversation History**
   - Store messages in format: [{"role": "user/assistant", "content": "..."}]
   - Pass full history to maintain context
   - Enables multi-turn dialogue

3. **Prompt Engineering**
   - Set clear role ("You are a respectful code tutor")
   - Provide context (experience level, preferences)
   - Specify exact output format (## Questions, ## Observations)
   - Give examples and guidelines

4. **Structured Output Parsing**
   - Look for section markers (## Headers)
   - Track parsing state (current_section)
   - Clean formatting (remove bullets, numbering)
   - Return structured data (lists, dicts)

5. **Error Handling**
   - Wrap API calls in try/except
   - Provide helpful error messages
   - Handle network, auth, and rate limit issues

6. **API Call Patterns**
   - model: Which AI model to use
   - max_tokens: Response length limit
   - messages: List of conversation messages
   - response.content[0].text: Extract text from response

7. **Facade Pattern**
   - Hide complex API details behind simple methods
   - analyze_code(), process_answers(), continue_conversation()
   - Makes calling code cleaner and more testable

🔧 PROMPT ENGINEERING TIPS:

**Structure a Good Prompt:**
```
1. Role: "You are a [specific role]"
2. Context: Provide all relevant information
3. Task: Clear, numbered steps
4. Format: Exact output format specification
5. Tone: Set the right attitude/approach
6. Examples: Show what good output looks like (if needed)
```

**Conversation History Format:**
```python
[
    {"role": "user", "content": "Initial question"},
    {"role": "assistant", "content": "Response"},
    {"role": "user", "content": "Follow-up"},
    {"role": "assistant", "content": "Further response"},
]
```

📚 FURTHER LEARNING:
- Anthropic API documentation
- Prompt engineering best practices
- LLM conversation patterns
- Structured output from LLMs
- Token limits and context windows
- Rate limiting and error handling
- Testing code that calls external APIs
