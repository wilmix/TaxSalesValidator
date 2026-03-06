# Repository Guidelines

## Project Structure & Module Organization
Core application code lives in `src/`. The main entry point is `src/main.py`, which orchestrates scraping, processing, validation, and optional SAS sync. Keep domain logic in focused modules (for example, `web_scraper.py`, `sales_validator.py`, `sas_syncer.py`).

Use `data/downloads/` for raw ZIP exports and `data/processed/` for generated CSV outputs. Store run artifacts and diagnostics in `logs/`. Long-form documentation belongs in `docs/`. Automated tests should go in `tests/`; repository-root `test_*.py` files are utility/integration scripts used manually.

## Build, Test, and Development Commands
- `uv sync`: install and lock dependencies from `pyproject.toml`/`uv.lock`.
- `uv run playwright install chromium`: install browser runtime required for scraping.
- `uv run python -m src.main`: run default monthly workflow.
- `uv run python -m src.main --year 2025 --month SEPTIEMBRE --debug`: run a specific period with verbose logs.
- `uv run python -m src.main --skip-scraping --csv-path "data/processed/<run>/archivoVentas.csv"`: process existing CSV without browser automation.
- `uv run pytest`: execute tests configured under `tests/`.
- `uv run black src/` and `uv run ruff check src/`: format and lint before opening a PR.

## Coding Style & Naming Conventions
Target Python 3.11+ with 4-space indentation and explicit type hints. Formatting is enforced by Black (line length 100), linting/import order by Ruff, and static checks by MyPy (strict options enabled in `pyproject.toml`).

Use `snake_case` for modules, functions, and variables; `PascalCase` for classes; `UPPER_CASE` for constants. Keep orchestration in `main.py` and reusable business logic in dedicated modules.

## Testing Guidelines
Write tests with Pytest using `test_*.py` naming and `Test*` class names. Place new automated tests in `tests/` so default discovery picks them up. For database/SAS connectivity checks, use the root helper scripts (for example, `uv run python test_db_connection.py`) and include results in PR notes.

## Commit & Pull Request Guidelines
Follow the existing conventional style in history: `feat:`, `fix:`, `docs:` (lowercase type + colon + concise summary). Keep commits scoped to one logical change.

PRs should include:
- clear purpose and impacted workflow phase(s),
- linked issue/ticket when applicable,
- test/lint evidence (command + outcome),
- screenshots or log excerpts for scraper/UI-flow changes.

## Security & Configuration Tips
Copy `.env.example` to `.env` and never commit secrets. Validate sensitive changes with `--dry-run` before real SAS sync. Avoid committing files from `data/processed/` or credential-bearing logs.
