"""Logging system for Code Tutor student interactions."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4


class SessionLogger:
    """Manages logging of student interactions for debugging and analysis."""

    def __init__(self, config_dir: Optional[Path] = None, enabled: bool = True):
        """Initialize the session logger.

        Args:
            config_dir: Optional custom configuration directory path.
            enabled: Whether logging is enabled.
        """
        self.enabled = enabled
        if config_dir is None:
            config_dir = Path.home() / ".config" / "code-tutor"

        self.log_dir = config_dir / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Current session data
        self.session_id = str(uuid4())
        self.session_start = datetime.utcnow().isoformat()
        self.session_type = None
        self.events: List[Dict[str, Any]] = []
        self.metadata: Dict[str, Any] = {}

        # Log file path (JSONL format for easy appending)
        self.log_file = self.log_dir / f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.session_id[:8]}.jsonl"

    def start_session(self, session_type: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Start a new logging session.

        Args:
            session_type: Type of session ('review' or 'teaching').
            metadata: Optional session metadata (e.g., file paths, config).
        """
        if not self.enabled:
            return

        self.session_type = session_type
        self.metadata = metadata or {}

        event = {
            "event_type": "session_start",
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": self.session_id,
            "session_type": session_type,
            "metadata": self.metadata,
        }

        self._log_event(event)

    def log_user_input(self, input_type: str, content: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Log user input.

        Args:
            input_type: Type of input ('answer', 'question', 'explanation', 'command').
            content: The user's input content.
            context: Optional context information.
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
        """Log AI response.

        Args:
            response_type: Type of response ('question', 'feedback', 'evaluation', 'code').
            content: The AI's response content.
            context: Optional context information.
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

    def log_code_analysis(self, file_path: str, code_content: str, analysis: str) -> None:
        """Log code analysis event.

        Args:
            file_path: Path to the analyzed file.
            code_content: The code that was analyzed.
            analysis: The analysis results.
        """
        if not self.enabled:
            return

        event = {
            "event_type": "code_analysis",
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": self.session_id,
            "file_path": file_path,
            "code_content": code_content,
            "analysis": analysis,
        }

        self._log_event(event)

    def log_teaching_round(self, round_num: int, topic: str, language: str,
                          flawed_code: str, student_explanation: str,
                          ai_evaluation: str) -> None:
        """Log a teaching mode round.

        Args:
            round_num: The round number.
            topic: The teaching topic.
            language: Programming language.
            flawed_code: The flawed code presented.
            student_explanation: Student's teaching explanation.
            ai_evaluation: AI's evaluation of the teaching.
        """
        if not self.enabled:
            return

        event = {
            "event_type": "teaching_round",
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": self.session_id,
            "round_number": round_num,
            "topic": topic,
            "language": language,
            "flawed_code": flawed_code,
            "student_explanation": student_explanation,
            "ai_evaluation": ai_evaluation,
        }

        self._log_event(event)

    def log_api_call(self, model: str, prompt: str, response: str,
                     usage: Optional[Dict[str, int]] = None) -> None:
        """Log an API call (if enabled in config).

        Args:
            model: The model used.
            prompt: The prompt sent to the API.
            response: The API response.
            usage: Optional usage statistics.
        """
        if not self.enabled:
            return

        event = {
            "event_type": "api_call",
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": self.session_id,
            "model": model,
            "prompt": prompt,
            "response": response,
            "usage": usage or {},
        }

        self._log_event(event)

    def log_error(self, error_type: str, message: str, traceback: Optional[str] = None) -> None:
        """Log an error.

        Args:
            error_type: Type of error.
            message: Error message.
            traceback: Optional traceback.
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

    def end_session(self) -> None:
        """End the current logging session."""
        if not self.enabled:
            return

        event = {
            "event_type": "session_end",
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": self.session_id,
            "duration_seconds": (datetime.utcnow() - datetime.fromisoformat(self.session_start)).total_seconds(),
        }

        self._log_event(event)

    def _log_event(self, event: Dict[str, Any]) -> None:
        """Write an event to the log file.

        Args:
            event: Event data to log.
        """
        self.events.append(event)

        # Write to JSONL file (one JSON object per line)
        try:
            with open(self.log_file, "a") as f:
                f.write(json.dumps(event) + "\n")
        except IOError as e:
            # If we can't write to the log file, store in memory only
            pass

    def export_session(self, output_path: Optional[Path] = None) -> Path:
        """Export the current session to a JSON file.

        Args:
            output_path: Optional output file path. If None, generates a default path.

        Returns:
            Path to the exported file.
        """
        if output_path is None:
            output_path = self.log_dir / f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.session_id[:8]}.json"

        session_data = {
            "session_id": self.session_id,
            "session_type": self.session_type,
            "start_time": self.session_start,
            "end_time": datetime.utcnow().isoformat(),
            "metadata": self.metadata,
            "events": self.events,
            "event_count": len(self.events),
        }

        with open(output_path, "w") as f:
            json.dump(session_data, f, indent=2)

        return output_path

    @staticmethod
    def export_all_logs(config_dir: Optional[Path] = None, output_path: Optional[Path] = None) -> Path:
        """Export all log files to a single JSON file.

        Args:
            config_dir: Optional custom configuration directory path.
            output_path: Optional output file path.

        Returns:
            Path to the exported file.
        """
        if config_dir is None:
            config_dir = Path.home() / ".config" / "code-tutor"

        log_dir = config_dir / "logs"

        if not log_dir.exists():
            # No logs to export
            if output_path is None:
                output_path = Path.cwd() / f"code_tutor_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

            with open(output_path, "w") as f:
                json.dump({"sessions": [], "total_sessions": 0}, f, indent=2)

            return output_path

        # Read all JSONL files
        sessions = []
        for log_file in sorted(log_dir.glob("session_*.jsonl")):
            events = []
            try:
                with open(log_file, "r") as f:
                    for line in f:
                        if line.strip():
                            events.append(json.loads(line))

                if events:
                    # Extract session info from first event
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
                # Skip files that can't be read
                continue

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

    @staticmethod
    def clear_logs(config_dir: Optional[Path] = None) -> int:
        """Clear all log files.

        Args:
            config_dir: Optional custom configuration directory path.

        Returns:
            Number of log files deleted.
        """
        if config_dir is None:
            config_dir = Path.home() / ".config" / "code-tutor"

        log_dir = config_dir / "logs"

        if not log_dir.exists():
            return 0

        count = 0
        for log_file in log_dir.glob("session_*.jsonl"):
            try:
                log_file.unlink()
                count += 1
            except OSError:
                pass

        return count
