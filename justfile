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
