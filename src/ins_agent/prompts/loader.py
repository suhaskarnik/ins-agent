"""Loads git-versioned Markdown prompt files.

Plain `.format()`-style `{variable}` substitution — no Jinja2. System
prompts live under `prompts/system/`; the eligibility Guideline (owned by
agent configuration, never suppliable by the Claimant) lives under
`prompts/guidelines/`.
"""

from pathlib import Path

_PROMPTS_DIR = Path(__file__).parent


def _read(subdir: str, name: str) -> str:
    return (_PROMPTS_DIR / subdir / f"{name}.md").read_text()


def load_system_prompt(name: str, **variables: str) -> str:
    template = _read("system", name)
    return template.format(**variables) if variables else template


def load_guideline(name: str) -> str:
    return _read("guidelines", name)
