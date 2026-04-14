# Agent Instructions for flysight2csv

This file provides guidance for AI coding agents (e.g. GitHub Copilot, Codex) working in this repository.

---

## Critical Rules for AI Agents

1. Update this file with any new instructions or conventions that future AI agents should follow when contributing to
   this project.

## Project Overview

**flysight2csv** is a Python CLI tool and library for finding and reformatting
[FlySight 2](https://flysight.ca/) GPS/sensor CSV files (`SENSOR.CSV` and `TRACK.CSV`).
It flattens the multi-header FlySight 2 format into standard CSV or JSON-Lines output suitable
for use with tools like pandas, csvkit, or Google Sheets.

- **Language:** Python 3.10+
- **Package manager:** [Poetry](https://python-poetry.org/) (`pyproject.toml` / `poetry.lock`)
- **Source layout:** `src/flysight2csv/` (PEP 517 src layout)
- **Docs:** Sphinx + MyST-Parser, hosted on [Read the Docs](https://flysight2csv.readthedocs.io)
- **Tests:** pytest with coverage

---

## Repository Layout

```
src/flysight2csv/       # Main package
  cli.py               # argparse CLI entry point (app())
  program.py           # Core program logic (Program class) - decoupled from CLI
  program_params.py    # Pydantic parameter models (ProgramParams and sub-models)
  parser.py            # FlySight 2 CSV parser (Parser, parse_csv)
  parsed.py            # Data structures for parsed output (ParsedCSV, DataRow, CSVMeta)
  reformatter.py       # Output formatters (csv-flat, json-lines-*)
  selection.py         # StringSelection helper (include/exclude filter)
  const.py             # Shared constants
  version.py           # __version__ string (managed by python-semantic-release)

tests/
  data/                # Test fixtures
    device1/ device2/  # Source FlySight 2 CSV files (truncated)
    complete/          # Complete (non-truncated) recordings
    formatted/         # Source files + expected reformatted output
    invalid/           # Files with format errors
    edge-cases/        # Edge-case files
    cli_expected/      # Expected CLI output (e.g. help.txt)
  conftest.py          # Auto-fail on logged warnings/errors fixture
  test_cli.py          # CLI integration tests
  test_parser.py       # Parser unit tests
  test_program.py      # Program logic tests
  test_writer.py       # Reformatter/writer tests
  test_python_module.py

docs/                  # Sphinx documentation (MyST Markdown)
  conf.py              # Sphinx config
  requirements.txt     # Docs-only pip requirements (sphinx<9, myst-parser, furo)
  *.md                 # Documentation pages
```

---

## Development Setup

```shell
# Install all dependencies (including dev group)
poetry install

# Install including docs dependencies
poetry install --with docs
```

Python 3.10+ is required. The project uses a `src/` layout so always run commands via
`poetry run` or activate the virtualenv first.

---

## Running Tests

**Always run tests after any code change.** All tests must pass.

```shell
# Run all tests (preferred)
poetry run pytest

# Run with coverage
poetry run pytest --cov=flysight2csv --cov-report=term-missing

# Run a specific test file
poetry run pytest tests/test_parser.py

# Run a specific test by name
poetry run pytest -k "test_strict_mode"
```

The `conftest.py` fixture **auto-fails any test that logs a warning or error** unless the
test is marked with `@pytest.mark.ignore_warnings`. Don't suppress warnings unless
intentional — fix the underlying issue.

---

## Linting and Formatting

```shell
# Run all pre-commit hooks (black, isort, ruff, mypy)
poetry run pre-commit run -a

# Or run tools individually:
poetry run black src/ tests/
poetry run isort src/ tests/
poetry run ruff check src/ tests/
poetry run mypy src/
```

Code style rules are in `pyproject.toml` under `[tool.black]`, `[tool.isort]`,
`[tool.ruff]`, and `[tool.mypy]`.

- Line length: **120**
- Target: Python 3.10+
- mypy: strict-ish; pydantic plugin enabled

---

## Building Docs Locally

```shell
# One-time build
poetry run python -m sphinx -b html docs docs/_build/html

# Auto-rebuild on changes
poetry run sphinx-autobuild docs docs/_build/html
```

**Important:** `docs/requirements.txt` pins `sphinx>=8,<9` because `myst-parser 4.x`
requires `sphinx>=7,<9`. Do not upgrade sphinx beyond `<9` until myst-parser supports it.

---

## Architecture Notes

### CLI ↔ Program separation

`cli.py` handles argument parsing and logging setup only. All logic lives in
`program.py` (`Program` class). This makes it easy to add a GUI or alternate CLI
framework without touching business logic.

### Pydantic parameter models

All user-configurable options are defined as Pydantic `BaseModel` subclasses in
`program_params.py`. `cli.py` parses args into grouped dicts and calls
`ProgramParams.model_validate(grouped_args)`. Always add new parameters to the
appropriate sub-model (`FinderParams`, `ParserOptions`, `ReformatParams`,
`OutputPathParams`, `UIParams`) and add the corresponding CLI argument in `cli.py`.

### Parser design

`Parser` (in `parser.py`) is a line-by-line stateful parser for the FlySight 2 format.
Key row types: `$FLYS` (header), `$VAR`, `$COL`, `$UNIT`, `$DATA`, `$TIME`.
`UnexpectedFormatError` is raised on format violations when strict mode is active.
`parse_csv(path, options)` is the main public entry point.

### Output formats

`Reformatter` (in `reformatter.py`) writes a `ParsedCSV` to a file handle.
Formats: `unchanged`, `csv-flat`, `json-lines-minimal`, `json-lines-header`, `json-lines-full`.
`EXTENSIONS` in `program_params.py` maps `FileFormats` → file extension.

### StringSelection

`StringSelection` (in `selection.py`) is used for include/exclude filters on sensor names
and column names. It accepts a list of strings (from CLI `--sensors` / `--columns`).

---

## Versioning and Releases

- Version is stored in **two places** kept in sync by `python-semantic-release`:
  - `pyproject.toml` → `[tool.poetry] version`
  - `src/flysight2csv/version.py` → `__version__`
- Releases are triggered automatically via a GitHub Actions workflow using
  [python-semantic-release](https://python-semantic-release.readthedocs.io/).
- Commit messages must follow **Conventional Commits** (`feat:`, `fix:`, `docs:`, etc.).
  `commitlint` runs on CI and (optionally) via pre-commit.

---

## Commit Message Convention

All commits **must** follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<optional scope>): <description>

Examples:
  feat(parser): support $BARO sensor type
  fix(cli): handle missing output directory gracefully
  docs: update usage examples
  test(reformatter): add edge case for empty rows
```

Allowed types: `build`, `chore`, `ci`, `docs`, `feat`, `fix`, `perf`, `style`, `refactor`, `test`.
Commits prefixed with `[copilot]` indicate AI-generated changes.

---

## Adding New Features — Checklist

1. Add/update the Pydantic model in `program_params.py`.
2. Add the CLI argument in `cli.py` (`get_argument_parser`).
3. Implement the logic in `program.py` or the appropriate module.
4. Add test fixtures under `tests/data/` if new file formats are needed.
5. Add/update tests in `tests/`.
6. Run `poetry run pytest` — all tests must pass.
7. Run `poetry run pre-commit run -a` — no lint errors.
8. Update `docs/` if the feature is user-facing.

---

## Common Gotchas

- **Output file handle must be opened with `newline=""` and `encoding="utf-8"`** — see
  `Reformatter.write_reformatted` docstring. The CSV writer handles line endings itself.
- **`parse_csv` returns a `ParsedCSV`** which can be combined via `sum(list_of_parsed, ParsedCSV())`.
- **Merge only happens when `--format` is not `unchanged`** and `--output-directory` is set.
- **Tests auto-fail on logged warnings** — if your code logs a warning in a test path,
  the test fails unless `@pytest.mark.ignore_warnings` is applied.
- **Directories starting with `_` are scratch/reference areas** — do not commit
  changes there unless explicitly asked.
