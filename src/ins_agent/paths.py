"""The repo root, computed once — modules that need a path relative to it
(seed data, Scenario fixtures, output, the diagram) import it from here
rather than each recomputing `Path(__file__).resolve().parents[N]`."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
