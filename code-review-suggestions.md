# Codebase Review Suggestions

## Findings (Ordered by Severity)
- **MED:** Exercise README suggests `code-tutor exercise submit {self.exercises_dir.name}/{topic}`, which won’t match the timestamped exercise IDs, so most submissions will fail; use the generated ID/path instead. (`src/code_tutor/exercise_manager.py:272`)
- **MED:** `api_key_locked` doesn’t prevent env‑var override, so a user can bypass the lock by setting `CODE_TUTOR_API_KEY`; decide whether locks should supersede env vars. (`src/code_tutor/config.py:230`, `src/code_tutor/config.py:343`)
- **MED:** Logging persists full user input and code content to disk; combined with export, this is a privacy leak risk unless explicitly consented to. Consider redaction/opt‑in/warnings. (`src/code_tutor/logger.py:61`, `src/code_tutor/logger.py:105`)
- **LOW:** “Understanding Achieved” parsing is case‑sensitive and brittle; model format drift can cause false negatives and extra rounds. Parse headings case‑insensitively or via a stricter delimiter. (`src/code_tutor/teaching_session.py:466`, `src/code_tutor/proof_session.py:730`)
- **LOW:** `log_api_calls` is a no‑op (config flag and logger method exist but are never used); wire it into API calls or remove it. (`src/code_tutor/config.py:335`, `src/code_tutor/logger.py:157`)
- **LOW:** Testing gap: pytest is declared but no tests exist; parsing and config merging are unguarded. Add unit tests for prompt parsing, file/proof readers, and config load/merge. (`pyproject.toml:42`)

## Open Questions / Assumptions
- Should `api_key_locked` enforce the key even against environment variables in shared deployments?
- Is it acceptable to store raw code and user input in logs by default, or should this be opt‑in?
- For directory reviews, do you want per‑file sessions in logs or a single aggregated session?

## Refactoring Opportunities
- Introduce a shared LLM client wrapper (retry/backoff, logging, response normalization) used by analyzer/session/generator classes.
- Centralize prompt templates + parsing helpers to remove duplicated parsing logic across code/proof/teaching flows.
- Use dataclasses (or pydantic) for config, metadata, and log events to validate inputs and reduce dict juggling.
- Factor out CLI config‑load/guard logic into a helper/decorator to cut repetition.

## Change Summary
- No code changes; review only.

## Next Steps
1. Implement the medium‑severity fixes and add a first round of unit tests.
2. Refactor the LLM client + prompt parsing + config models first.
