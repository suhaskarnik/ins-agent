set dotenv-load

# Start the local Postgres instance.
up:
    podman compose -f podman-compose.yml up -d

# Tear down the local Postgres instance, including its volume.
down:
    podman compose -f podman-compose.yml down -v

# Regenerate the fixed-seed fake Policy dataset and load it into Postgres.
seed:
    uv run python -m ins_agent.db.seed

# Truncate the LLM response cache.
cache-clear:
    uv run python -c "from ins_agent.db.cache import clear_cache; clear_cache()"

# Lint the codebase.
lint:
    uv run ruff check .

# Type-check the codebase.
typecheck:
    uv run mypy src

# Run the interactive TUI: prompts for claim details field-by-field.
run:
    uv run python -m ins_agent.cli.run

# Replay a Scenario's Intake Input non-interactively, end-to-end.
run-scenario SCENARIO:
    uv run python -m ins_agent.cli.run_scenario {{SCENARIO}}

# Run the test suite.
test:
    uv run pytest

# Drift check: re-run the Eligibility Judgment / Sufficiency Assessment
# steps for each Scenario against their recorded golden outputs. Separate
# from `just test` — a mismatch is a signal, not a hard regression gate.
eval:
    uv run python -m ins_agent.cli.eval

# Regenerate docs/graph.mmd from the compiled LangGraph.
diagram:
    uv run python -m ins_agent.cli.diagram

push:
		git push origin main
