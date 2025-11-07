"""
Logging system for Code Tutor student interactions.

📚 FILE OVERVIEW:
This file implements a logging system that records student interactions for
debugging and analysis. It uses JSONL (JSON Lines) format for efficient
append-only logging.

🎯 WHAT YOU'LL LEARN:
- JSONL format for logging (one JSON object per line)
- Event-based logging architecture
- Session tracking with UUIDs
- Timestamp management with ISO format
- Exporting and aggregating log files

💡 WHY THIS FILE EXISTS:
When building educational software, you need to track:
- What questions were asked
- How students responded
- What feedback was provided
- Errors that occurred
This helps debug issues and understand student learning patterns.
"""

# ============================================================================
# IMPORTS
# ============================================================================

import json  # 🔍 For JSON encoding/decoding
import os  # For file system operations (used implicitly)
from datetime import datetime  # 🎯 Timestamp generation
from pathlib import Path  # Modern file path handling
from typing import Any, Dict, List, Optional  # Type hints
from uuid import uuid4  # 💡 Generate unique session IDs


# ============================================================================
# SessionLogger CLASS
# ============================================================================

class SessionLogger:
    """
    Manages logging of student interactions for debugging and analysis.

    🔍 DESIGN PATTERN: Event Logger
    Records discrete events (user input, AI response, errors) with timestamps.

    💡 JSONL FORMAT:
    Each line is a complete JSON object. This allows:
    - Efficient appending (no need to rewrite entire file)
    - Easy streaming (process line by line)
    - Fault tolerance (corrupted line doesn't break entire file)

    🎯 EVENT TYPES LOGGED:
    - session_start/end: Session boundaries
    - user_input: Student's questions, answers, commands
    - ai_response: Questions, feedback, evaluations from Claude
    - code_analysis: Analysis results
    - teaching_round: Teaching mode rounds
    - api_call: Raw API calls (optional, can be verbose)
    - error: Exceptions and errors
    """

    def __init__(self, config_dir: Optional[Path] = None, enabled: bool = True):
        """
        Initialize the session logger.

        🔍 CREATES UNIQUE SESSION:
        Each logger instance represents one session with a unique ID.

        Args:
            config_dir: Configuration directory (defaults to ~/.config/code-tutor).
            enabled: Whether logging is enabled.
        """
        self.enabled = enabled

        # Set up log directory
        if config_dir is None:
            config_dir = Path.home() / ".config" / "code-tutor"
        self.log_dir = config_dir / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)  # Create if doesn't exist

        # ========================================
        # SESSION INITIALIZATION
        # ========================================
        # 🔍 uuid4() generates a random UUID like "f47ac10b-58cc-4372-a567-0e02b2c3d479"
        self.session_id = str(uuid4())

        # 💡 ISO format timestamp: "2025-01-15T14:30:00.123456"
        # utcnow() uses UTC (avoids timezone issues)
        self.session_start = datetime.utcnow().isoformat()

        self.session_type = None  # "review" or "teaching"
        self.events: List[Dict[str, Any]] = []  # In-memory event storage
        self.metadata: Dict[str, Any] = {}  # Session metadata

        # ========================================
        # LOG FILE PATH
        # ========================================
        # 🎯 Format: session_20250115_143000_f47ac10b.jsonl
        # This makes files sortable and identifiable
        self.log_file = self.log_dir / f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.session_id[:8]}.jsonl"

    # ------------------------------------------------------------------------
    # SESSION LIFECYCLE
    # ------------------------------------------------------------------------

    def start_session(self, session_type: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Start a new logging session.

        💡 RECORDS INITIAL STATE:
        Logs session type, start time, and metadata (file path, config, etc.).

        Args:
            session_type: Type of session ('review' or 'teaching').
            metadata: Optional session metadata.
        """
        if not self.enabled:
            return  # If logging disabled, do nothing

        self.session_type = session_type
        self.metadata = metadata or {}

        # Create session start event
        event = {
            "event_type": "session_start",
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": self.session_id,
            "session_type": session_type,
            "metadata": self.metadata,
        }

        self._log_event(event)

    def end_session(self) -> None:
        """
        End the current logging session.

        💡 CALCULATES DURATION:
        Computes how long the session lasted.
        """
        if not self.enabled:
            return

        # Calculate session duration
        duration = (datetime.utcnow() - datetime.fromisoformat(self.session_start)).total_seconds()

        event = {
            "event_type": "session_end",
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": self.session_id,
            "duration_seconds": duration,
        }

        self._log_event(event)

    # ------------------------------------------------------------------------
    # EVENT LOGGING METHODS
    # ------------------------------------------------------------------------
    # 🔍 Each method logs a specific type of event with relevant context

    def log_user_input(self, input_type: str, content: str, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Log user input.

        Args:
            input_type: Type ('answer', 'question', 'explanation', 'command').
            content: The user's input content.
            context: Optional context (question number, etc.).
        """
        if not self.enabled:
            return

        event = {
            "event_type": "user_input",
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": self.session_id,
            "input_type": input_type,
            "content": content,
            "context": context or {},
        }

        self._log_event(event)

    def log_ai_response(self, response_type: str, content: str, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Log AI response.

        Args:
            response_type: Type ('question', 'feedback', 'evaluation', 'code').
            content: The AI's response content.
            context: Optional context.
        """
        if not self.enabled:
            return

        event = {
            "event_type": "ai_response",
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": self.session_id,
            "response_type": response_type,
            "content": content,
            "context": context or {},
        }

        self._log_event(event)

    def log_error(self, error_type: str, message: str, traceback: Optional[str] = None) -> None:
        """
        Log an error.

        💡 CRITICAL FOR DEBUGGING:
        Errors are logged even if they're handled, helping identify patterns.

        Args:
            error_type: Type of error (FileNotFoundError, ValueError, etc.).
            message: Error message.
            traceback: Optional traceback string.
        """
        if not self.enabled:
            return

        event = {
            "event_type": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": self.session_id,
            "error_type": error_type,
            "message": message,
            "traceback": traceback,
        }

        self._log_event(event)

    # ------------------------------------------------------------------------
    # INTERNAL EVENT WRITING
    # ------------------------------------------------------------------------

    def _log_event(self, event: Dict[str, Any]) -> None:
        """
        Write an event to the log file.

        🔍 JSONL FORMAT:
        Each event is written as one line: JSON object + newline

        💡 DUAL STORAGE:
        - Appends to file (persistent)
        - Stores in memory (for quick access during session)

        Args:
            event: Event data to log.
        """
        # Store in memory
        self.events.append(event)

        # Write to file
        # 🎯 Mode 'a' = append (don't overwrite)
        try:
            with open(self.log_file, "a") as f:
                # Write JSON + newline
                # 💡 json.dumps() converts dict to JSON string
                f.write(json.dumps(event) + "\n")
        except IOError:
            # If we can't write, just keep in memory
            # ⚠️ Silent failure - could enhance with fallback
            pass

    # ------------------------------------------------------------------------
    # STATIC EXPORT METHODS
    # ------------------------------------------------------------------------
    # 💡 @staticmethod means these don't need an instance to call

    @staticmethod
    def export_all_logs(config_dir: Optional[Path] = None, output_path: Optional[Path] = None) -> Path:
        """
        Export all log files to a single JSON file.

        🔍 AGGREGATES ALL SESSIONS:
        Reads all JSONL files and combines into one JSON file.

        💡 USE CASE:
        Send logs to instructor/developer for debugging.

        Args:
            config_dir: Config directory.
            output_path: Output file path.

        Returns:
            Path to exported file.
        """
        if config_dir is None:
            config_dir = Path.home() / ".config" / "code-tutor"

        log_dir = config_dir / "logs"

        if not log_dir.exists():
            # No logs exist - create empty export
            if output_path is None:
                output_path = Path.cwd() / f"code_tutor_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

            with open(output_path, "w") as f:
                json.dump({"sessions": [], "total_sessions": 0}, f, indent=2)

            return output_path

        # ========================================
        # READ ALL JSONL FILES
        # ========================================
        sessions = []

        # 🔍 glob() finds all files matching pattern
        for log_file in sorted(log_dir.glob("session_*.jsonl")):
            events = []

            try:
                # Read line by line (JSONL format)
                with open(log_file, "r") as f:
                    for line in f:
                        if line.strip():  # Skip empty lines
                            events.append(json.loads(line))

                if events:
                    # Extract session info from first and last events
                    first_event = events[0]
                    last_event = events[-1]

                    session_data = {
                        "session_id": first_event.get("session_id"),
                        "session_type": first_event.get("session_type"),
                        "start_time": first_event.get("timestamp"),
                        "end_time": last_event.get("timestamp"),
                        "metadata": first_event.get("metadata", {}),
                        "events": events,
                        "event_count": len(events),
                        "log_file": str(log_file.name),
                    }
                    sessions.append(session_data)

            except (IOError, json.JSONDecodeError):
                # Skip files that can't be read or parsed
                continue

        # ========================================
        # WRITE COMBINED EXPORT
        # ========================================
        if output_path is None:
            output_path = Path.cwd() / f"code_tutor_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        export_data = {
            "export_timestamp": datetime.utcnow().isoformat(),
            "total_sessions": len(sessions),
            "sessions": sessions,
        }

        with open(output_path, "w") as f:
            json.dump(export_data, f, indent=2)

        return output_path


# ============================================================================
# KEY TAKEAWAYS
# ============================================================================
"""
🎓 WHAT YOU LEARNED:

1. **JSONL Format**
   - One JSON object per line
   - Efficient for append-only logging
   - Easy to stream and process

2. **Event-Based Logging**
   - Discrete events with timestamps
   - Different event types for different actions
   - Structured data with context

3. **UUID for Session Tracking**
   - uuid4() generates unique IDs
   - Helps correlate events across distributed systems
   - Makes sessions identifiable

4. **ISO Timestamps**
   - datetime.utcnow().isoformat()
   - Sortable, unambiguous format
   - UTC avoids timezone confusion

5. **Dual Storage**
   - Events in memory (fast access during session)
   - Events on disk (persistent)
   - Trade-off: memory vs. durability

6. **Static Methods for Utilities**
   - Don't need instance state
   - export_all_logs() works on all sessions
   - clear_logs() cleans up

7. **Error Handling**
   - Silent failure in _log_event (don't break app)
   - Skip corrupt files in export
   - Always check file existence

📚 FURTHER LEARNING:
- JSON Lines (JSONL) specification
- Structured logging best practices
- Log aggregation systems
- UUID generation and uses
- Datetime and timezone handling
"""
