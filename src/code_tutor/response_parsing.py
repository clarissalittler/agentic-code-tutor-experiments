"""Helpers for parsing structured model responses."""

import json
import re
from typing import Any, Dict, List, Optional


def extract_json_object(response: str) -> Optional[Dict[str, Any]]:
    """Extract the first valid JSON object found in a model response."""
    if not response or not response.strip():
        return None

    stripped = response.strip()

    # Fast path: response is raw JSON.
    direct = _parse_json_dict(stripped)
    if direct is not None:
        return direct

    # Common path: response wraps JSON in a fenced code block.
    for candidate in _extract_json_fenced_candidates(stripped):
        parsed = _parse_json_dict(candidate)
        if parsed is not None:
            return parsed

    # Fallback: scan for balanced {...} fragments and try each candidate.
    for candidate in _extract_brace_object_candidates(stripped):
        parsed = _parse_json_dict(candidate)
        if parsed is not None:
            return parsed

    return None


def parse_string_list(data: Dict[str, Any], key: str) -> List[str]:
    """Extract a cleaned list of strings from `data[key]`."""
    raw = data.get(key, [])
    if isinstance(raw, list):
        items = raw
    elif isinstance(raw, str):
        items = [raw]
    else:
        return []

    cleaned: List[str] = []
    for item in items:
        text = str(item).strip()
        if text:
            cleaned.append(text)
    return cleaned


def parse_string_value(data: Dict[str, Any], key: str, default: str = "") -> str:
    """Extract a cleaned string value from `data[key]`."""
    value = data.get(key)
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def parse_bool_value(data: Dict[str, Any], key: str) -> Optional[bool]:
    """Extract a boolean value from `data[key]`, accepting YES/NO strings."""
    value = data.get(key)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"yes", "true"}:
            return True
        if lowered in {"no", "false"}:
            return False
    return None


def parse_understanding_achieved(response: str) -> Optional[bool]:
    """Parse an Understanding Achieved YES/NO marker from a model response."""
    if not response:
        return None

    parsed_json = extract_json_object(response)
    if parsed_json:
        parsed_bool = parse_bool_value(parsed_json, "understanding_achieved")
        if parsed_bool is not None:
            return parsed_bool

    inline_match = re.search(
        r"understanding achieved\s*[:\-]?\s*(yes|no)\b",
        response,
        re.IGNORECASE,
    )
    if inline_match:
        return inline_match.group(1).lower() == "yes"

    heading_match = re.search(
        r"^#{1,6}\s*understanding achieved\b.*$",
        response,
        re.IGNORECASE | re.MULTILINE,
    )
    if not heading_match:
        return None

    tail = response[heading_match.end():].lstrip(" \t:\n\r")
    if not tail:
        return None

    first_line = tail.splitlines()[0] if tail else ""
    parsed = _parse_yes_no(first_line)
    if parsed is not None:
        return parsed

    return _parse_yes_no(tail)


def _extract_json_fenced_candidates(text: str) -> List[str]:
    pattern = re.compile(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", re.IGNORECASE)
    return [match.group(1) for match in pattern.finditer(text)]


def _extract_brace_object_candidates(text: str) -> List[str]:
    candidates: List[str] = []
    depth = 0
    start_index: Optional[int] = None

    for index, char in enumerate(text):
        if char == "{":
            if depth == 0:
                start_index = index
            depth += 1
        elif char == "}":
            if depth == 0:
                continue
            depth -= 1
            if depth == 0 and start_index is not None:
                candidates.append(text[start_index:index + 1])
                start_index = None

    return candidates


def _parse_json_dict(candidate: str) -> Optional[Dict[str, Any]]:
    try:
        parsed = json.loads(candidate)
    except (json.JSONDecodeError, TypeError):
        return None

    if isinstance(parsed, dict):
        return parsed
    return None


def _parse_yes_no(text: str) -> Optional[bool]:
    if re.search(r"\byes\b", text, re.IGNORECASE):
        return True
    if re.search(r"\bno\b", text, re.IGNORECASE):
        return False
    return None
