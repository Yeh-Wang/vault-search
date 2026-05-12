# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install project and all dependencies (creates venv + lockfile automatically)
uv sync

# Run full test suite
uv run pytest -v

# Run a single test file or test
uv run pytest tests/test_parser.py -v
uv run pytest tests/test_parser.py::test_parse_markdown_frontmatter_headings_tags_and_links -v

# Run the CLI tool
uv run vlt index --root /path/to/vault
uv run vlt search "query" --root /path/to/vault --json
uv run vlt health --root /path/to/vault --json

# Config management
uv run vlt config set default_root /path/to/vault
uv run vlt config list
uv run vlt config path
```

## Architecture

This is a local-first CLI tool for full-text search over Obsidian vaults. It indexes Markdown files into SQLite + FTS5 and provides a single `vlt` CLI entry point with subcommands: `index`, `search`, `health`, `config`.

**Pipeline:** `discovery` → `parser` → `indexer` (which calls `database`)

- **`discovery.py`** — walks a vault root for `*.md` files, skips ignored dirs (`.obsidian/`, `.git/`, `tmp/`, `.venv/`, `node_modules/`, `.trash/`, `.pytest_cache/`). Returns `DiscoveredFile` objects with `relative_path`, `area` (top-level dir or `"root"`), and `mtime`.
- **`parser.py`** — parses a single Markdown file into a `Document` dataclass. Extracts: YAML frontmatter (title, tags), headings (`#`), wikilinks (`[[target|alias]]`), inline tags (`#tag`). Title resolution: first heading > frontmatter `title:` > filename stem. Supports Chinese characters in inline tags.
- **`models.py`** — frozen dataclasses: `Document`, `Heading`, `Link`. These are the canonical data types flowing through the pipeline.
- **`indexer.py`** — orchestrates discovery + parsing + link resolution, then calls `rebuild_database()`. Link resolution matches wikilink targets against document paths, titles, and stems (in that order), stripping `#section` fragments.
- **`database.py`** — SQLite schema management, full-text search, and health queries. Uses FTS5 for keyword search with a Chinese-friendly `LIKE` fallback (triggered when FTS5 returns nothing for CJK queries). Schema: `documents`, `document_tags`, `headings`, `wikilinks`, `documents_fts` (virtual), `index_meta`.
- **`cli.py`** — argparse subcommands under `vlt` entry point. `--root` sets vault path (implies default DB path `<vault>/tmp/vault-search.sqlite`). `--db` overrides the DB path directly. Root resolution: CLI `--root` > auto-detect `.obsidian/` from cwd > global config `default_root`. Auto-builds index when database missing. Errors in helpers use `_CliError` exception, caught in `main()` for clean exit codes.
- **`config.py`** — configuration management. Global config at `~/.config/vault-search/config.json`, project config at `<vault>/.obsidian/vault-search.json`. `resolve_root()` implements the priority chain. `resolve_setting()` merges project > global settings. `detect_vault_root()` walks up from cwd looking for `.obsidian/`.

**Default DB path:** `<vault_root>/tmp/vault-search.sqlite`

## Key conventions

- Codebase targets Python >= 3.10, uses `from __future__ import annotations` everywhere.
- Package uses `src` layout (`src/vault_search/`), configured via `pyproject.toml` with setuptools.
- Tests use `tmp_path` fixture for isolation and `sample_vault` (conftest) for a realistic multi-file vault structure.
- Config system: global (`~/.config/vault-search/config.json`) + project (`<vault>/.obsidian/vault-search.json`). No env vars.
- The index is a full rebuild every time (no incremental indexing in v1).
