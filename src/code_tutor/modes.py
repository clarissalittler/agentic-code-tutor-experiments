"""Mode metadata used by CLI surfaces and documentation output."""

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class ModeDefinition:
    """Describes a user-facing mode."""

    command: str
    title: str
    summary: str


CORE_MODES: Tuple[ModeDefinition, ...] = (
    ModeDefinition(
        command="review",
        title="Code Review",
        summary="Interactive code review with clarifying questions and tailored feedback.",
    ),
    ModeDefinition(
        command="teach-me",
        title="Teach Me",
        summary="Socratic learning by diagnosing intentionally flawed code examples.",
    ),
    ModeDefinition(
        command="roguelike",
        title="Roguelike",
        summary="Generate homework-style coding runs you can solve and grade later.",
    ),
)

EXTENDED_MODES: Tuple[ModeDefinition, ...] = (
    ModeDefinition(
        command="proof",
        title="Proof",
        summary="Review and practice mathematical proofs in informal and formal formats.",
    ),
)

COMMAND_ALIASES = {
    "exercise": "roguelike",
}


def get_core_modes() -> Tuple[ModeDefinition, ...]:
    """Return the primary learning modes."""
    return CORE_MODES


def get_all_modes() -> Tuple[ModeDefinition, ...]:
    """Return all available mode groups."""
    return CORE_MODES + EXTENDED_MODES
